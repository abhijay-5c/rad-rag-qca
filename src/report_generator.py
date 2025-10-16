import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to Python path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
from config.prompts import (
    OBSERVATIONS_SYSTEM_PROMPT,
    OBSERVATIONS_HUMAN_PROMPT_TEMPLATE,
    IMPRESSION_SYSTEM_PROMPT,
    IMPRESSION_HUMAN_PROMPT_TEMPLATE,
    TECHNIQUE_TEMPLATES
)

# Load environment variables
load_dotenv('pws.env')

class RadiologyReportGenerator:
    def __init__(self):
        """Initialize the report generator with GPT-4o-mini"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    
    def generate_technique_section(self, mod_study: str) -> str:
        """Generate technique section based on study type"""
        return TECHNIQUE_TEMPLATES.get(mod_study, f"CT images of {mod_study} were obtained.")
    
    def organize_findings_by_anatomy(self, findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize findings by anatomical regions"""
        anatomy_groups = {
            "LUNGS": [],
            "MEDIASTINUM": [],
            "PLEURA": [],
            "HEART": [],
            "VASCULATURE": [],
            "UPPER ABDOMEN": [],
            "SKELETAL PROCESS": [],
            "SOFT TISSUES": [],
            "SPINE": [],
            "NECK": [],
            "HEAD": []
        }
        
        # Map categories to anatomical regions
        category_mapping = {
            "Lungs": "LUNGS",
            "Airways": "LUNGS",
            "Pleura": "PLEURA",
            "Heart": "HEART",
            "Pericardium": "HEART",
            "Vessels": "VASCULATURE",
            "Vasculature": "VASCULATURE",
            "Mediastinum": "MEDIASTINUM",
            "Lymph Nodes": "MEDIASTINUM",
            "Abdomen": "UPPER ABDOMEN",
            "Bones": "SKELETAL PROCESS",
            "Spine": "SPINE",
            "Soft Tissues": "SOFT TISSUES",
            "Neck": "NECK",
            "Head": "HEAD"
        }
        
        for finding in findings:
            category = finding.get('category', '')
            mapped_region = category_mapping.get(category, 'SOFT TISSUES')
            anatomy_groups[mapped_region].append(finding)
        
        # Remove empty groups
        return {k: v for k, v in anatomy_groups.items() if v}
    
    def generate_observations_section(
        self, 
        findings: List[Dict[str, Any]], 
        mod_study: str, 
        case_metadata: Dict[str, Any],
        all_answers: List[Dict[str, Any]] = None,
        study_chunks: List[str] = None
    ) -> str:
        """Generate observations section from findings with full context
        
        Args:
            findings: Positive findings (answer='Yes')
            mod_study: Study type
            case_metadata: Case information
            all_answers: ALL answers including negative findings (NEW)
            study_chunks: Study protocol chunks (NEW)
        """
        
        # Group positive findings by subcategory
        findings_by_region = {}
        for finding in findings:
            # Include ALL findings where answer is 'Yes', even if details are empty
            region = finding.get('subcategory', 'Other')
            if region not in findings_by_region:
                findings_by_region[region] = []
            
            # If details are provided, use them; otherwise just use the question
            details_text = finding.get('details', '').strip()
            if not details_text:
                # No details provided - just note that the finding is present
                details_text = "Present (no additional details provided)"
            
            findings_by_region[region].append({
                'question': finding.get('question', ''),
                'details': details_text
            })
        
        # Group negative findings by subcategory (NEW)
        negative_findings_by_region = {}
        if all_answers:
            for answer in all_answers:
                if answer.get('answer') == 'No':
                    region = answer.get('subcategory', 'Other')
                    if region not in negative_findings_by_region:
                        negative_findings_by_region[region] = []
                    negative_findings_by_region[region].append({
                        'question': answer.get('question', '')
                    })
        
        # Prepare study protocol context (NEW)
        study_protocol_context = ""
        if study_chunks:
            # Combine chunks into concise protocol summary
            study_protocol_context = "\n\n".join(study_chunks[:3])  # Use first 3 chunks for context
        
        system_prompt = OBSERVATIONS_SYSTEM_PROMPT
        
        # Enhanced human prompt with all context
        human_prompt = OBSERVATIONS_HUMAN_PROMPT_TEMPLATE.format(
            mod_study=mod_study,
            clinical_history=case_metadata.get('clinical_history', 'Not specified'),
            findings_json=json.dumps(findings_by_region, indent=2)
        )
        
        # Add negative findings context
        if negative_findings_by_region:
            human_prompt += f"\n\n**NEGATIVE FINDINGS (Specifically Evaluated and Found Normal):**\n{json.dumps(negative_findings_by_region, indent=2)}"
        
        # Add study protocol context
        if study_protocol_context:
            human_prompt += f"\n\n**STUDY PROTOCOL REFERENCE (for systematic review):**\n{study_protocol_context}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"Error generating observations: {str(e)}")
            return "Error generating observations section."
    
    def generate_impression_section(self, findings: List[Dict[str, Any]], case_metadata: Dict[str, Any]) -> str:
        """Generate impression section from findings and case metadata"""
        
        # Get all findings where answer is 'Yes' (regardless of details)
        positive_findings = [f for f in findings if f.get('answer') == 'Yes']
        
        if not positive_findings:
            return "No significant abnormalities identified on the current study."
        
        system_prompt = IMPRESSION_SYSTEM_PROMPT
        
        # Extract findings for impression
        findings_text = []
        for f in positive_findings:
            details = f.get('details', '').strip()
            if details:
                findings_text.append(f"{f.get('question', '')}: {details}")
            else:
                findings_text.append(f"{f.get('question', '')}: Present")
        
        mod_study = case_metadata.get('mod_study', 'Unknown')
        
        human_prompt = IMPRESSION_HUMAN_PROMPT_TEMPLATE.format(
            mod_study=mod_study,
            clinical_history=case_metadata.get('clinical_history', 'Not specified'),
            age=case_metadata.get('age', 'Not specified'),
            gender=case_metadata.get('gender', 'Not specified'),
            findings_text=chr(10).join(findings_text)
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            print(f"Error generating impression: {str(e)}")
            return "Error generating impression section."
    
    def generate_complete_report(
        self, 
        case_metadata: Dict[str, Any], 
        findings: List[Dict[str, Any]],
        all_answers: List[Dict[str, Any]] = None,
        study_chunks: List[str] = None
    ) -> Dict[str, Any]:
        """Generate a complete radiology report with full context
        
        Args:
            case_metadata: Patient and case information
            findings: Positive findings (answer='Yes')
            all_answers: ALL answers including negative findings (NEW)
            study_chunks: Study protocol chunks from vector DB (NEW)
        """
        mod_study = case_metadata.get('mod_study', '')
        
        # Use all_answers if provided, otherwise fall back to findings
        if all_answers is None:
            all_answers = findings
        
        # Generate each section with enhanced context
        history = case_metadata.get('clinical_history', 'Not specified')
        technique = self.generate_technique_section(mod_study)
        observations = self.generate_observations_section(
            findings=findings,
            mod_study=mod_study,
            case_metadata=case_metadata,
            all_answers=all_answers,      # NEW: Pass all answers
            study_chunks=study_chunks      # NEW: Pass study chunks
        )
        impression = self.generate_impression_section(findings, case_metadata)
        
        # Create the complete report
        report = {
            "case_id": case_metadata.get('case_id', f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "patient_info": {
                "age": case_metadata.get('age', 'Not specified'),
                "gender": case_metadata.get('gender', 'Not specified')
            },
            "study_type": mod_study,
            "report": {
                "history": history,
                "technique": technique,
                "observations": observations,
                "impression": impression
            },
            "findings": findings
        }
        
        return report
    
    def format_report_for_display(self, report: Dict[str, Any]) -> str:
        """Format the report for display"""
        formatted_report = f"""
# RADIOLOGY REPORT

**Case ID:** {report['case_id']}
**Date:** {report['date']}
**Patient:** {report['patient_info']['age']} year old {report['patient_info']['gender']}
**Study:** {report['study_type']}

## History
{report['report']['history']}

## Technique
{report['report']['technique']}

## Observations
{report['report']['observations']}

## Impression
{report['report']['impression']}
"""
        return formatted_report
    
    def save_report(self, report: Dict[str, Any]) -> str:
        """Save report to file"""
        try:
            case_id = report['case_id']
            filename = f"data/report_{case_id}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Also save formatted version
            formatted_filename = f"data/report_{case_id}.txt"
            with open(formatted_filename, 'w') as f:
                f.write(self.format_report_for_display(report))
            
            return filename
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            return ""
    
    def load_report(self, case_id: str) -> Dict[str, Any]:
        """Load report from file"""
        try:
            filename = f"data/report_{case_id}.json"
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading report: {str(e)}")
            return {}

class ReportDatabase:
    def __init__(self, db_file: str = "data/reports.db"):
        """Initialize report database"""
        self.db_file = db_file
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for reports"""
        import sqlite3
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                case_id TEXT PRIMARY KEY,
                date TEXT,
                patient_age TEXT,
                patient_gender TEXT,
                study_type TEXT,
                clinical_history TEXT,
                report_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_report(self, report: Dict[str, Any]) -> bool:
        """Save report to database"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO reports 
                (case_id, date, patient_age, patient_gender, study_type, clinical_history, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                report['case_id'],
                report['date'],
                report['patient_info']['age'],
                report['patient_info']['gender'],
                report['study_type'],
                report['report']['history'],
                json.dumps(report)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving report to database: {str(e)}")
            return False
    
    def get_all_reports(self) -> List[Dict[str, Any]]:
        """Get all reports from database"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM reports ORDER BY created_at DESC')
            rows = cursor.fetchall()
            
            reports = []
            for row in rows:
                report = json.loads(row[6])  # report_json column
                reports.append(report)
            
            conn.close()
            return reports
        except Exception as e:
            print(f"Error loading reports from database: {str(e)}")
            return []
    
    def get_report(self, case_id: str) -> Dict[str, Any]:
        """Get specific report by case ID"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT report_json FROM reports WHERE case_id = ?', (case_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return json.loads(row[0])
            return {}
        except Exception as e:
            print(f"Error loading report from database: {str(e)}")
            return {}

def main():
    """Test the report generator"""
    generator = RadiologyReportGenerator()
    
    # Test case metadata and findings
    case_metadata = {
        "case_id": "test_001",
        "age": "65",
        "gender": "Male",
        "clinical_history": "Chest pain and shortness of breath",
        "mod_study": "ct_chest"
    }
    
    test_findings = [
        {
            "category": "Lungs",
            "subcategory": "Parenchyma",
            "item": "nodules",
            "details": "Multiple centrilobular nodules in bilateral lungs with tree-in-bud pattern"
        },
        {
            "category": "Lungs",
            "subcategory": "Parenchyma", 
            "item": "emphysema",
            "details": "Centriacinar emphysematous changes in bilateral lungs"
        },
        {
            "category": "Pleura",
            "subcategory": "Effusion",
            "item": "pleural effusion",
            "details": "Right-sided pleural effusion with subsegmental collapse"
        }
    ]
    
    print("Generating report...")
    report = generator.generate_complete_report(case_metadata, test_findings)
    
    print("Report generated successfully!")
    print(generator.format_report_for_display(report))
    
    # Save report
    filename = generator.save_report(report)
    print(f"Report saved to: {filename}")

if __name__ == "__main__":
    main()

