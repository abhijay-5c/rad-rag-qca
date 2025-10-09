import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to Python path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from src.vector_db_setup import CTVectorDatabase
from dotenv import load_dotenv
from config.prompts import (
    CHECKLIST_SYSTEM_PROMPT,
    CHECKLIST_HUMAN_PROMPT_TEMPLATE,
    FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT,
    FOLLOW_UP_QUESTIONS_HUMAN_PROMPT_TEMPLATE
)

# Load environment variables
load_dotenv('pws.env')

class RadiologyChecklistGenerator:
    def __init__(self):
        """Initialize the checklist generator with GPT-4o-mini"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.vector_db = CTVectorDatabase()
    
    def get_study_chunks(self, mod_study: str) -> List[str]:
        """Retrieve all chunks for a specific study"""
        try:
            results = self.vector_db.get_chunks_by_study_only(mod_study)
            if results and results['documents']:
                return results['documents']
            return []
        except Exception as e:
            print(f"Error retrieving chunks for {mod_study}: {str(e)}")
            return []
    
    def generate_checklist(self, case_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured checklist based on case metadata and study content"""
        
        mod_study = case_metadata.get('mod_study', '')
        study_chunks = self.get_study_chunks(mod_study)
        
        if not study_chunks:
            return {"error": f"No chunks found for study: {mod_study}"}
        
        # Combine all chunks into a single context
        study_content = "\n\n".join(study_chunks)
        
        # Create the prompt for checklist generation
        system_prompt = CHECKLIST_SYSTEM_PROMPT
        
        human_prompt = CHECKLIST_HUMAN_PROMPT_TEMPLATE.format(
            age=case_metadata.get('age', 'Not specified'),
            gender=case_metadata.get('gender', 'Not specified'),
            clinical_history=case_metadata.get('clinical_history', 'Not specified'),
            mod_study=mod_study,
            study_content=study_content
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Try to extract JSON from the response
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            print(f"LLM Response: {response_text[:200]}...")  # Debug print
            
            checklist_json = json.loads(response_text)
            return checklist_json
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {str(e)}")
            print(f"Raw response: {response_text}")
            return {"error": "Failed to generate valid checklist JSON"}
        except Exception as e:
            print(f"Error generating checklist: {str(e)}")
            return {"error": f"Failed to generate checklist: {str(e)}"}
    
    def save_checklist(self, checklist: Dict[str, Any], case_id: str) -> str:
        """Save checklist to file"""
        try:
            filename = f"data/checklist_{case_id}.json"
            with open(filename, 'w') as f:
                json.dump(checklist, f, indent=2)
            return filename
        except Exception as e:
            print(f"Error saving checklist: {str(e)}")
            return ""
    
    def load_checklist(self, case_id: str) -> Dict[str, Any]:
        """Load checklist from file"""
        try:
            filename = f"data/checklist_{case_id}.json"
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading checklist: {str(e)}")
            return {}

class InteractiveQASystem:
    def __init__(self):
        """Initialize the interactive Q&A system"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.current_category = 0
        self.current_subcategory = 0
        self.current_item = 0
        self.answers = {}
        self.findings = []
    
    def reset_session(self):
        """Reset the Q&A session"""
        self.current_category = 0
        self.current_subcategory = 0
        self.current_item = 0
        self.answers = {}
        self.findings = []
    
    def get_next_question(self, checklist: Dict[str, Any]) -> Dict[str, Any]:
        """Get the next question based on current progress"""
        if "checklist" not in checklist:
            return {"error": "Invalid checklist format"}
        
        categories = checklist["checklist"]
        
        if self.current_category >= len(categories):
            return {"status": "completed", "message": "All questions completed"}
        
        current_cat = categories[self.current_category]
        subcategories = current_cat.get("subcategories", [])
        
        if self.current_subcategory >= len(subcategories):
            # Move to next category
            self.current_category += 1
            self.current_subcategory = 0
            self.current_item = 0
            return self.get_next_question(checklist)
        
        current_subcat = subcategories[self.current_subcategory]
        items = current_subcat.get("items", [])
        
        if self.current_item >= len(items):
            # Move to next subcategory
            self.current_subcategory += 1
            self.current_item = 0
            return self.get_next_question(checklist)
        
        current_item = items[self.current_item]
        
        return {
            "status": "question",
            "category": current_cat["category"],
            "subcategory": current_subcat["name"],
            "item": current_item,
            "question": f"Are there any findings related to: {current_item}?",
            "progress": {
                "category": self.current_category + 1,
                "total_categories": len(categories),
                "subcategory": self.current_subcategory + 1,
                "total_subcategories": len(subcategories),
                "item": self.current_item + 1,
                "total_items": len(items)
            }
        }
    
    def process_answer(self, answer: str, details: str = "") -> Dict[str, Any]:
        """Process user's answer and generate follow-up questions if needed"""
        question_data = self.get_current_question_data()
        
        if not question_data:
            return {"error": "No current question data"}
        
        # Store the answer
        answer_key = f"{question_data['category']}_{question_data['subcategory']}_{question_data['item']}"
        self.answers[answer_key] = {
            "answer": answer.lower(),
            "details": details,
            "category": question_data['category'],
            "subcategory": question_data['subcategory'],
            "item": question_data['item']
        }
        
        # If answer is positive, generate follow-up questions
        if answer.lower() in ['yes', 'y', 'positive', 'present']:
            follow_up = self.generate_follow_up_questions(question_data, details)
            if follow_up:
                return {
                    "status": "follow_up",
                    "follow_up_questions": follow_up,
                    "current_finding": {
                        "category": question_data['category'],
                        "subcategory": question_data['subcategory'],
                        "item": question_data['item'],
                        "details": details
                    }
                }
        
        # Move to next question
        self.current_item += 1
        return {"status": "next_question"}
    
    def get_current_question_data(self) -> Dict[str, Any]:
        """Get current question data for processing answers"""
        # This would be set by the get_next_question method
        return getattr(self, '_current_question_data', None)
    
    def set_current_question_data(self, data: Dict[str, Any]):
        """Set current question data"""
        self._current_question_data = data
    
    def generate_follow_up_questions(self, question_data: Dict[str, Any], details: str) -> List[str]:
        """Generate follow-up questions for positive findings"""
        system_prompt = FOLLOW_UP_QUESTIONS_SYSTEM_PROMPT
        
        human_prompt = FOLLOW_UP_QUESTIONS_HUMAN_PROMPT_TEMPLATE.format(
            item=question_data['item'],
            category=question_data['category'],
            subcategory=question_data['subcategory'],
            details=details
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            follow_up_questions = json.loads(response.content)
            return follow_up_questions
        except Exception as e:
            print(f"Error generating follow-up questions: {str(e)}")
            return []
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        positive_findings = []
        for key, answer_data in self.answers.items():
            if answer_data['answer'] in ['yes', 'y', 'positive', 'present']:
                positive_findings.append({
                    "category": answer_data['category'],
                    "subcategory": answer_data['subcategory'],
                    "item": answer_data['item'],
                    "details": answer_data['details']
                })
        
        return {
            "total_questions": len(self.answers),
            "positive_findings": positive_findings,
            "progress": {
                "category": self.current_category,
                "subcategory": self.current_subcategory,
                "item": self.current_item
            }
        }

def main():
    """Test the checklist generator"""
    generator = RadiologyChecklistGenerator()
    
    # Test case metadata
    case_metadata = {
        "age": "65",
        "gender": "Male",
        "clinical_history": "Chest pain and shortness of breath",
        "mod_study": "ct_chest"
    }
    
    print("Generating checklist...")
    checklist = generator.generate_checklist(case_metadata)
    
    if "error" in checklist:
        print(f"Error: {checklist['error']}")
    else:
        print("Checklist generated successfully!")
        print(json.dumps(checklist, indent=2))
        
        # Save checklist
        case_id = "test_case_001"
        filename = generator.save_checklist(checklist, case_id)
        print(f"Checklist saved to: {filename}")

if __name__ == "__main__":
    main()
