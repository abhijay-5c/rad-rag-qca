#!/usr/bin/env python3
"""
Test script for report generation with sample findings
"""
import sys
import os
from pathlib import Path
import json

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.report_generator import RadiologyReportGenerator

def main():
    # Sample findings data
    findings = [
        {
            "question": "Are there any abnormalities in Lung Parenchyma?",
            "category": "Lungs",
            "subcategory": "Lung Parenchyma",
            "item": "screening_1",
            "details": "Mild fibrotic changes are seen in the bilateral lung field with atelectasis bans are seen in right lower lobe"
        },
        {
            "question": "Are there any abnormalities in Pleural Assessment?",
            "category": "Pleura",
            "subcategory": "Pleural Assessment",
            "item": "screening_2",
            "details": "Mild plueral effusion noted in the right lower lobe"
        },
        {
            "question": "Are there any abnormalities in Neck Structures?",
            "category": "Lower Neck and Supraclavicular Region",
            "subcategory": "Neck Structures",
            "item": "screening_6",
            "details": "Bilateral thyroid is enlaregd in size with hyperdense seen small calcifed node is noted in right lower lobe measuring ~ 7 x 7 mm"
        },
        {
            "question": "Are there any abnormalities in Visceral Assessment?",
            "category": "Abdomen",
            "subcategory": "Visceral Assessment",
            "item": "screening_7",
            "details": "the visuvalised liver is mildy enlarged in size"
        },
        {
            "question": "Are there any signs of emphysema or cystic changes in the lungs that were not previously mentioned?",
            "category": "Lungs",
            "subcategory": "Lung Parenchyma",
            "item": "specific_1_3",
            "details": ""
        },
        {
            "question": "Are there any pulmonary nodules, either solid or ground glass, in addition to the previously noted abnormalities in the lung parenchyma?",
            "category": "Lungs",
            "subcategory": "Lung Parenchyma",
            "item": "specific_1_6",
            "details": ""
        }
    ]
    
    # Case metadata
    case_metadata = {
        "case_id": "test_report_001",
        "age": "65",
        "gender": "Male",
        "clinical_history": "Breathing difficulty and wet cough with body swelling",
        "mod_study": "ct_chest"
    }
    
    print("=" * 80)
    print("TESTING REPORT GENERATION")
    print("=" * 80)
    print(f"\nCase ID: {case_metadata['case_id']}")
    print(f"Study: {case_metadata['mod_study']}")
    print(f"Clinical History: {case_metadata['clinical_history']}")
    print(f"\nFindings provided: {len(findings)}")
    print("\n" + "=" * 80)
    print()
    
    # Initialize report generator
    print("Initializing report generator...")
    generator = RadiologyReportGenerator()
    
    # Generate report
    print("Generating report...\n")
    report = generator.generate_complete_report(case_metadata, findings)
    
    # Display formatted report
    print("=" * 80)
    print("GENERATED REPORT")
    print("=" * 80)
    print()
    
    formatted_report = generator.format_report_for_display(report)
    print(formatted_report)
    
    print("\n" + "=" * 80)
    print("OBSERVATIONS SECTION (detailed)")
    print("=" * 80)
    print(report['report']['observations'])
    
    print("\n" + "=" * 80)
    print("IMPRESSION SECTION (detailed)")
    print("=" * 80)
    print(report['report']['impression'])
    
    # Save report
    print("\n" + "=" * 80)
    filename = generator.save_report(report)
    print(f"Report saved to: {filename}")
    print("=" * 80)

if __name__ == "__main__":
    main()



