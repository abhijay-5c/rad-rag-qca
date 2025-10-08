import json
import os
from typing import Dict, List, Any
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

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
        technique_templates = {
            "ct_chest": "Volume scan of chest was done without IV contrast.",
            "ct_head": "Axial CT images of the head were obtained without IV contrast.",
            "ct_lumbar_spine": "Axial and sagittal CT images of the lumbar spine were obtained.",
            "ct_cervical_spine": "Axial and sagittal CT images of the cervical spine were obtained.",
            "ct_thoracic_spine": "Axial and sagittal CT images of the thoracic spine were obtained.",
            "ct_soft_tissue_neck": "Axial CT images of the neck soft tissues were obtained.",
            "ct_temporal_bone": "High-resolution CT images of the temporal bones were obtained."
        }
        
        return technique_templates.get(mod_study, f"CT images of {mod_study} were obtained.")
    
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
    
    def generate_observations_section(self, findings: List[Dict[str, Any]], mod_study: str, case_metadata: Dict[str, Any]) -> str:
        """Generate observations section from findings"""
        
        # Group positive findings by subcategory
        findings_by_region = {}
        for finding in findings:
            if finding.get('details') and finding.get('details').strip():
                region = finding.get('subcategory', 'Other')
                if region not in findings_by_region:
                    findings_by_region[region] = []
                findings_by_region[region].append({
                    'question': finding.get('question', ''),
                    'details': finding['details']
                })
        
        system_prompt = """You are an expert radiologist writing the OBSERVATIONS section of a radiology report.

CRITICAL RULES:
1. Write in proper radiology report format with anatomical regions as headers (ALL CAPS)
2. ONLY describe POSITIVE findings (abnormalities that were identified)
3. For each finding, write complete, detailed descriptions including:
   - Specific location and laterality
   - Size/extent with measurements
   - Characteristics (density/signal, morphology)
   - Associated findings
4. DO NOT list negative findings or say "appears normal" for every region
5. Write in past tense ("is seen", "are noted", "appears")
6. Use standard radiological terminology
7. Be specific and quantitative

Format example:
LUNGS:
Multiple centrilobular nodules are seen in bilateral lungs with tree-in-bud pattern.

PLEURA:
Right-sided pleural effusion measuring approximately 200ml in volume is noted.

If NO positive findings, write: "No significant abnormalities identified on the current study."
"""
        
        human_prompt = f"""
Study Type: {mod_study}
Clinical History: {case_metadata.get('clinical_history', 'Not specified')}

Positive Findings by Region:
{json.dumps(findings_by_region, indent=2)}

Generate the OBSERVATIONS section. Only describe the positive findings provided. Do not invent findings or list negative findings.
"""
        
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
        
        # Get only findings with details
        positive_findings = [f for f in findings if f.get('details') and f.get('details').strip()]
        
        if not positive_findings:
            return "No significant abnormalities identified on the current study."
        
        system_prompt = """You are an expert radiologist writing the IMPRESSION section of a radiology report.

CRITICAL RULES:
1. Provide a concise summary of KEY POSITIVE findings only
2. Correlate findings with clinical history
3. Provide clinical significance and differential diagnosis when appropriate
4. Write in clear, professional radiological language
5. Do NOT list negative findings
6. Suggest follow-up or additional studies if clinically appropriate

Format:
- Start with the most significant findings
- Provide clinical context and interpretation
- End with recommendations if needed

Example:
"Acute subarachnoid hemorrhage along the left frontal lobe sulci.

Post-operative changes with craniectomy defect involving left frontal bones and underlying gliotic changes.

Old fractures involving left posterior maxillary wall, zygomatic arch, lateral orbital wall and frontal bone."
"""
        
        # Extract just the details for impression
        findings_text = []
        for f in positive_findings:
            findings_text.append(f"{f.get('question', '')}: {f['details']}")
        
        mod_study = case_metadata.get('mod_study', 'Unknown')
        
        human_prompt = f"""
Study Type: {mod_study}
Clinical History: {case_metadata.get('clinical_history', 'Not specified')}
Age: {case_metadata.get('age', 'Not specified')}
Gender: {case_metadata.get('gender', 'Not specified')}

Positive Findings:
{chr(10).join(findings_text)}

Generate a concise, clinically relevant IMPRESSION that:
1. Summarizes the key findings
2. Correlates with the clinical history
3. Provides clinical significance
4. Suggests differential diagnosis or follow-up if appropriate
"""
        
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
    
    def generate_complete_report(self, case_metadata: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a complete radiology report"""
        mod_study = case_metadata.get('mod_study', '')
        
        # Generate each section
        history = case_metadata.get('clinical_history', 'Not specified')
        technique = self.generate_technique_section(mod_study)
        observations = self.generate_observations_section(findings, mod_study, case_metadata)
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
            filename = f"report_{case_id}.json"
            
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Also save formatted version
            formatted_filename = f"report_{case_id}.txt"
            with open(formatted_filename, 'w') as f:
                f.write(self.format_report_for_display(report))
            
            return filename
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            return ""
    
    def load_report(self, case_id: str) -> Dict[str, Any]:
        """Load report from file"""
        try:
            filename = f"report_{case_id}.json"
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading report: {str(e)}")
            return {}

class ReportDatabase:
    def __init__(self, db_file: str = "reports.db"):
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

