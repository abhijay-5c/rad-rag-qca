#!/usr/bin/env python3
"""
Demo script showing the complete radiology checklist and report generation workflow
"""

import json
from checklist_generator import RadiologyChecklistGenerator, InteractiveQASystem
from report_generator import RadiologyReportGenerator, ReportDatabase

def demo_complete_workflow():
    """Demonstrate the complete workflow from case input to final report"""
    
    print("🏥 Radiology Checklist and Report Generation System Demo")
    print("=" * 60)
    
    # Step 1: Case Input
    print("\n📝 Step 1: Case Input")
    case_metadata = {
        "case_id": "demo_001",
        "age": "65",
        "gender": "Male", 
        "clinical_history": "Chest pain and shortness of breath",
        "mod_study": "ct_chest"
    }
    
    print(f"Case ID: {case_metadata['case_id']}")
    print(f"Patient: {case_metadata['age']} year old {case_metadata['gender']}")
    print(f"History: {case_metadata['clinical_history']}")
    print(f"Study: {case_metadata['mod_study']}")
    
    # Step 2: Generate Checklist
    print("\n📋 Step 2: Generate Checklist")
    print("Retrieving study chunks and generating checklist...")
    
    generator = RadiologyChecklistGenerator()
    checklist = generator.generate_checklist(case_metadata)
    
    if "error" in checklist:
        print(f"❌ Error: {checklist['error']}")
        return
    
    print("✅ Checklist generated successfully!")
    print(f"Categories: {len(checklist['checklist'])}")
    
    # Show checklist structure
    for i, category in enumerate(checklist['checklist']):
        print(f"  {i+1}. {category['category']}")
        for subcat in category['subcategories']:
            print(f"     - {subcat['name']} ({len(subcat['items'])} items)")
    
    # Step 3: Interactive Q&A Simulation
    print("\n❓ Step 3: Interactive Q&A Simulation")
    print("Simulating user responses to checklist questions...")
    
    qa_session = InteractiveQASystem()
    
    # Simulate some answers
    simulated_answers = [
        ("yes", "Multiple centrilobular nodules in bilateral lungs with tree-in-bud pattern"),
        ("no", ""),
        ("yes", "Centriacinar emphysematous changes in bilateral lungs"),
        ("no", ""),
        ("yes", "Right-sided pleural effusion with subsegmental collapse"),
        ("no", ""),
        ("no", ""),
        ("no", ""),
        ("no", ""),
        ("no", "")
    ]
    
    findings = []
    question_count = 0
    
    for answer, details in simulated_answers:
        question_data = qa_session.get_next_question(checklist)
        
        if question_data.get("status") == "completed":
            break
        
        if question_data.get("status") == "question":
            question_count += 1
            print(f"  Q{question_count}: {question_data['question']}")
            print(f"     Category: {question_data['category']} > {question_data['subcategory']}")
            print(f"     Answer: {answer.upper()}")
            
            if answer.lower() == "yes" and details:
                print(f"     Details: {details}")
                findings.append({
                    "category": question_data['category'],
                    "subcategory": question_data['subcategory'],
                    "item": question_data['item'],
                    "details": details
                })
            
            qa_session.set_current_question_data(question_data)
            qa_session.process_answer(answer, details)
    
    print(f"\n✅ Q&A completed! {question_count} questions answered")
    print(f"Positive findings identified: {len(findings)}")
    
    # Step 4: Generate Report
    print("\n📄 Step 4: Generate Radiology Report")
    print("Generating final radiology report...")
    
    report_generator = RadiologyReportGenerator()
    report = report_generator.generate_complete_report(case_metadata, findings)
    
    print("✅ Report generated successfully!")
    
    # Display the report
    print("\n" + "="*60)
    print("FINAL RADIOLOGY REPORT")
    print("="*60)
    
    formatted_report = report_generator.format_report_for_display(report)
    print(formatted_report)
    
    # Step 5: Save to Database
    print("\n💾 Step 5: Save to Database")
    db = ReportDatabase()
    if db.save_report(report):
        print("✅ Report saved to database successfully!")
    else:
        print("❌ Error saving report to database")
    
    # Step 6: Summary
    print("\n📊 Workflow Summary")
    print("="*30)
    print(f"✅ Case metadata processed")
    print(f"✅ Checklist generated ({len(checklist['checklist'])} categories)")
    print(f"✅ Interactive Q&A completed ({question_count} questions)")
    print(f"✅ {len(findings)} positive findings identified")
    print(f"✅ Radiology report generated")
    print(f"✅ Report saved to database")
    
    print(f"\n🎯 Demo completed successfully!")
    print(f"Report file: report_{case_metadata['case_id']}.json")
    print(f"Checklist file: checklist_{case_metadata['case_id']}.json")

def demo_multiple_studies():
    """Demo with different study types"""
    
    print("\n\n🔄 Testing Multiple Study Types")
    print("="*40)
    
    test_cases = [
        {
            "case_id": "demo_head_001",
            "age": "45",
            "gender": "Female",
            "clinical_history": "Head trauma after fall",
            "mod_study": "ct_head"
        },
        {
            "case_id": "demo_spine_001", 
            "age": "72",
            "gender": "Male",
            "clinical_history": "Lower back pain with radiculopathy",
            "mod_study": "ct_lumbar_spine"
        }
    ]
    
    generator = RadiologyChecklistGenerator()
    
    for case in test_cases:
        print(f"\n📋 Testing {case['mod_study']} checklist generation...")
        checklist = generator.generate_checklist(case)
        
        if "error" not in checklist:
            print(f"✅ {case['mod_study']} checklist generated successfully!")
            print(f"   Categories: {len(checklist['checklist'])}")
        else:
            print(f"❌ Error with {case['mod_study']}: {checklist['error']}")

if __name__ == "__main__":
    try:
        demo_complete_workflow()
        demo_multiple_studies()
    except Exception as e:
        print(f"❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
