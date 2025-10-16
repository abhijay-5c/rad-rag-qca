import sys
import os
from pathlib import Path

# Add parent directory to Python path so we can import config and src modules
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import streamlit as st
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import pandas as pd
import json
from datetime import datetime
from config.prompts import (
    HIERARCHICAL_QUESTIONS_SYSTEM_PROMPT,
    HIERARCHICAL_QUESTIONS_EXAMPLE,
    HIERARCHICAL_QUESTIONS_HUMAN_PROMPT_TEMPLATE,
    FALLBACK_QUESTIONS,
    QUESTION_REFINEMENT_PROMPT_TEMPLATE
)

# Load environment variables
load_dotenv('/home/ai-user/rag-report-qcs-generation/pws.env')

def generate_hierarchical_questions_from_checklist(checklist, study_type):
    """Generate hierarchical questions from checklist using LLM"""
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
        
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.2,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        system_prompt = HIERARCHICAL_QUESTIONS_SYSTEM_PROMPT
        
        human_prompt = HIERARCHICAL_QUESTIONS_HUMAN_PROMPT_TEMPLATE.format(
            study_type=study_type,
            checklist_json=json.dumps(checklist, indent=2),
            example_output=HIERARCHICAL_QUESTIONS_EXAMPLE
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = llm.invoke(messages)
        response_text = response.content.strip()
        
        print(f"Raw LLM response: {response_text[:300]}...")
        
        # Clean up the response
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()
        elif response_text.startswith('```'):
            response_text = response_text.replace('```', '').strip()
        
        # Parse JSON
        questions = json.loads(response_text)
        
        # Validate structure
        if not isinstance(questions, list):
            print(f"ERROR: LLM returned {type(questions)} instead of list")
            return get_fallback_questions(study_type)
        
        if len(questions) == 0:
            print("ERROR: LLM returned empty list")
            return get_fallback_questions(study_type)
        
        print(f"Successfully generated {len(questions)} questions")
        return questions
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        print(f"Response was: {response_text[:500]}")
        return get_fallback_questions(study_type)
    except Exception as e:
        print(f"Error generating hierarchical questions: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback to basic questions
        return get_fallback_questions(study_type)

def get_fallback_questions(study_type):
    """Fallback questions if dynamic generation fails - returns proper dict structure"""
    return FALLBACK_QUESTIONS

def convert_item_to_question(item, category, subcategory):
    """Convert checklist item to proper clinical question - SIMPLIFIED VERSION"""
    
    # For now, just return None to skip all checklist items
    # We'll use predefined clinical questions instead
    return None

# Initialize Streamlit
st.set_page_config(
    page_title="CT Study Retrieval System",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 CT Study Retrieval System")
st.markdown("Interactive Radiology Checklist and Report Generation")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", [
    "Search", 
    "Browse by Study", 
    "Database Statistics",
    "Upload New Study",
    "Case Input",
    "Interactive Checklist",
    "Report Generation",
    "Report History"
])

# Initialize vector database connection
@st.cache_resource
def get_vector_db():
    try:
        client = chromadb.PersistentClient(path="./data/chroma_db")
        collection = client.get_collection("ct_studies")
        return collection
    except Exception as e:
        st.error(f"Error connecting to vector database: {str(e)}")
        return None

def get_all_studies():
    """Get list of all studies"""
    collection = get_vector_db()
    if not collection:
        return []
    
    try:
        results = collection.get()
        studies = set()
        for metadata in results['metadatas']:
            studies.add(metadata['study'])
        return sorted(list(studies))
    except Exception as e:
        st.error(f"Error retrieving studies: {str(e)}")
        return []

# Page routing
if page == "Search":
    st.header("🔍 Search CT Study Chunks")
    st.write("This is the search page - functionality coming soon!")

elif page == "Browse by Study":
    st.header("📚 Browse CT Studies")
    studies = get_all_studies()
    
    if studies:
        selected_study = st.selectbox("Select a study to browse:", studies)
        if st.button("Load Study Chunks"):
            st.write(f"Loading chunks for {selected_study}...")
    else:
        st.warning("No studies found in the database.")

elif page == "Database Statistics":
    st.header("📊 Database Statistics")
    st.write("Database statistics will be displayed here.")

elif page == "Upload New Study":
    st.header("📤 Upload New Study")
    st.markdown("Upload a new CT study PDF to add it to the vector database")
    
    with st.form("upload_form"):
        # File uploader
        uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            modality = st.selectbox("Modality", ["CT", "MRI", "X-Ray", "Ultrasound"])
            study_name = st.text_input("Study Name", placeholder="e.g., ct_abdomen, ct_pelvis")
        
        with col2:
            chunk_size = st.number_input("Chunk Size (characters)", min_value=500, max_value=2000, value=1000)
            chunk_overlap = st.number_input("Chunk Overlap (characters)", min_value=50, max_value=500, value=200)
        
        submitted = st.form_submit_button("Upload and Process", type="primary")
        
        if submitted:
            if uploaded_file is None:
                st.error("Please select a PDF file to upload.")
            elif not study_name:
                st.error("Please provide a study name.")
            else:
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        # Save uploaded file temporarily
                        temp_pdf_path = f"temp_{uploaded_file.name}"
                        with open(temp_pdf_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Process the PDF
                        from src.vector_db_setup import CTVectorDatabase
                        from langchain.text_splitter import RecursiveCharacterTextSplitter
                        from langchain_community.document_loaders import PyPDFLoader
                        
                        # Initialize vector DB
                        vector_db = CTVectorDatabase()
                        
                        # Update text splitter with custom parameters
                        vector_db.text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap,
                            length_function=len,
                            separators=["\n\n", "\n", " ", ""]
                        )
                        
                        # Extract text
                        loader = PyPDFLoader(temp_pdf_path)
                        pages = loader.load()
                        text = "\n".join([page.page_content for page in pages])
                        
                        # Split into chunks
                        chunks = vector_db.text_splitter.split_text(text)
                        
                        # Prepare documents with metadata
                        documents = []
                        for i, chunk in enumerate(chunks):
                            doc = {
                                "content": chunk,
                                "metadata": {
                                    "modality": modality,
                                    "study": study_name,
                                    "chunk_id": i,
                                    "source": uploaded_file.name
                                }
                            }
                            documents.append(doc)
                        
                        # Add to vector database
                        vector_db.add_documents_to_collection(documents)
                        
                        # Clean up temp file
                        import os
                        os.remove(temp_pdf_path)
                        
                        # Clear cache to refresh study list
                        st.cache_resource.clear()
                        
                        st.success(f"✅ Successfully processed {uploaded_file.name}!")
                        st.info(f"Added {len(documents)} chunks to vector database")
                        st.metric("Study Name", study_name)
                        st.metric("Chunks Created", len(documents))
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Error processing PDF: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
    
    # Show current studies
    st.subheader("Current Studies in Database")
    studies = get_all_studies()
    if studies:
        st.write(f"Total studies: {len(studies)}")
        for study in studies:
            st.write(f"- {study}")
    else:
        st.write("No studies found in database.")

elif page == "Case Input":
    st.header("📝 Case Input")
    st.markdown("Enter case metadata to start the radiology checklist process")
    
    with st.form("case_input_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.text_input("Age", placeholder="e.g., 65")
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        
        with col2:
            clinical_history = st.text_area("Clinical History", placeholder="e.g., Chest pain and shortness of breath")
            studies = get_all_studies()
            mod_study = st.selectbox("Study Type", studies if studies else ["ct_chest", "ct_head", "ct_lumbar_spine"])
        
        case_id = st.text_input("Case ID (optional)", placeholder="Leave blank for auto-generation")
        
        submitted = st.form_submit_button("Save Case Data", type="primary")
        
        if submitted:
            if not age or not clinical_history or not mod_study:
                st.error("Please fill in all required fields (Age, Clinical History, Study Type)")
            else:
                # Generate case ID if not provided
                if not case_id:
                    case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                case_metadata = {
                    "case_id": case_id,
                    "age": age,
                    "gender": gender,
                    "clinical_history": clinical_history,
                    "mod_study": mod_study
                }
                
                # Clear all previous session state for a fresh start
                st.session_state.case_metadata = case_metadata
                st.session_state.checklist_generated = False
                st.session_state.checklist = None
                st.session_state.questions_generated = False
                st.session_state.generated_questions = []
                st.session_state.screening_answers = {}
                st.session_state.current_question = 0
                st.session_state.answers = {}
                st.session_state.findings = []
                
                st.success(f"✅ Case metadata saved! Case ID: {case_id}")
                st.success(f"🔄 Session cleared - ready for new case")
                st.info("Go to 'Interactive Checklist' page to generate and start the checklist process.")

elif page == "Interactive Checklist":
    st.header("📋 Interactive Checklist")
    
    if 'case_metadata' not in st.session_state:
        st.warning("Please enter case metadata in the 'Case Input' page first.")
    else:
        case_metadata = st.session_state.case_metadata
        
        # Display case info
        st.subheader("Case Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Case ID", case_metadata['case_id'])
        with col2:
            st.metric("Age", case_metadata['age'])
        with col3:
            st.metric("Gender", case_metadata['gender'])
        
        st.info(f"**Study:** {case_metadata['mod_study']} | **History:** {case_metadata['clinical_history']}")
        
        # Add reset button
        if st.session_state.get('checklist_generated', False):
            col_reset, col_spacer = st.columns([1, 4])
            with col_reset:
                if st.button("🔄 Start Over"):
                    # Clear checklist and questions
                    st.session_state.checklist_generated = False
                    st.session_state.checklist = None
                    st.session_state.questions_generated = False
                    st.session_state.generated_questions = []
                    st.session_state.screening_answers = {}
                    st.session_state.current_question = 0
                    st.session_state.answers = {}
                    st.success("Session reset! Click 'Generate Checklist' to start over.")
                    st.rerun()
        
        # Generate checklist if not already generated
        if not st.session_state.get('checklist_generated', False):
            st.warning(f"⚠️ No checklist generated yet for study type: **{case_metadata['mod_study']}**")
            if st.button("Generate Checklist", type="primary"):
                with st.spinner(f"Generating checklist for {case_metadata['mod_study']} from study content..."):
                    try:
                        from src.checklist_generator import RadiologyChecklistGenerator
                        generator = RadiologyChecklistGenerator()
                        
                        st.info(f"🔍 Retrieving {case_metadata['mod_study']} protocol from vector database...")
                        checklist = generator.generate_checklist(case_metadata)
                        
                        if "error" in checklist:
                            st.error(f"❌ Error generating checklist: {checklist['error']}")
                            st.error(f"💡 Make sure the study type '{case_metadata['mod_study']}' exists in the documents/ folder")
                        else:
                            st.session_state.checklist = checklist
                            st.session_state.checklist_generated = True
                            st.session_state.qa_session = None
                            st.session_state.current_question = 0
                            st.session_state.answers = {}
                            st.success(f"✅ Checklist generated successfully for {case_metadata['mod_study']}!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        import traceback
                        with st.expander("🐛 Debug Info"):
                            st.code(traceback.format_exc())
        else:
            # Display checklist and start Q&A
            checklist = st.session_state.checklist
            
            # Show checklist structure
            with st.expander("📋 Generated Checklist Structure", expanded=False):
                st.json(checklist)
            
            # Simple Q&A Interface
            st.subheader("Interactive Q&A")
            
            if 'answers' not in st.session_state:
                st.session_state.answers = {}
            
            if 'current_question' not in st.session_state:
                st.session_state.current_question = 0
            
            # Generate hierarchical questions from the checklist
            if not st.session_state.get('questions_generated', False):
                with st.spinner("Generating hierarchical clinical questions from checklist..."):
                    hierarchical_questions = generate_hierarchical_questions_from_checklist(checklist, case_metadata['mod_study'])
                    st.session_state.generated_questions = hierarchical_questions
                    st.session_state.questions_generated = True
                    st.session_state.screening_answers = {}
                    st.success(f"Generated {len(hierarchical_questions)} hierarchical questions!")
            else:
                hierarchical_questions = st.session_state.generated_questions
            
            # Build question flow based on screening answers
            if 'screening_answers' not in st.session_state:
                st.session_state.screening_answers = {}
            
            # Debug: Check what we got
            if not isinstance(hierarchical_questions, list):
                st.error(f"Error: Expected list of questions, got {type(hierarchical_questions)}")
                st.code(str(hierarchical_questions))
                st.stop()
            
            if hierarchical_questions and not isinstance(hierarchical_questions[0], dict):
                st.error(f"Error: Expected dict objects in questions list, got {type(hierarchical_questions[0])}")
                st.code(str(hierarchical_questions[:3]))
                st.stop()
            
            all_questions = []
            
            # NEW FLOW: Group questions by screening question (region-by-region)
            # Build list of all screening questions first
            screening_questions = [q for q in hierarchical_questions if isinstance(q, dict) and q.get('type') == 'screening']
            
            # For each screening question, add it and its dependent specific questions
            for screening_q in screening_questions:
                screening_id = screening_q.get('id', '')
                
                # Add the screening question
                all_questions.append(screening_q)
                
                # If this screening was answered "Yes", immediately add all its specific questions
                if screening_id in st.session_state.screening_answers:
                    if st.session_state.screening_answers[screening_id] == 'Yes':
                        # Find all specific questions that depend on this screening question
                        specific_qs = [
                            q for q in hierarchical_questions 
                            if isinstance(q, dict) 
                            and q.get('type') == 'specific' 
                            and q.get('depends_on') == screening_id
                        ]
                        # Add them right after the screening question
                        all_questions.extend(specific_qs)
            
            total_questions = len(all_questions)
            current_q = st.session_state.current_question
            
            if current_q < total_questions:
                question_data = all_questions[current_q]
                
                # Refine question based on previous context (for specific questions)
                if question_data.get('type') == 'specific' and st.session_state.answers:
                    # Get previous positive findings for context
                    previous_findings = []
                    for ans in st.session_state.answers.values():
                        if ans['answer'] == 'Yes' and ans['details']:
                            previous_findings.append(f"{ans['question']}: {ans['details']}")
                    
                    if previous_findings and not st.session_state.get(f'refined_{current_q}', False):
                        # Refine the question with context
                        try:
                            from langchain_openai import ChatOpenAI
                            from langchain.schema import HumanMessage, SystemMessage
                            
                            llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.1, openai_api_key=os.getenv("OPENAI_API_KEY"))
                            
                            context_prompt = QUESTION_REFINEMENT_PROMPT_TEMPLATE.format(
                                previous_findings=chr(10).join(previous_findings),
                                current_question=question_data['question']
                            )
                            
                            response = llm.invoke([HumanMessage(content=context_prompt)])
                            refined_question = response.content.strip()
                            question_data['question'] = refined_question
                            st.session_state[f'refined_{current_q}'] = True
                        except:
                            pass  # Use original question if refinement fails
                
                # Progress bar
                progress = current_q / total_questions
                st.progress(progress)
                st.caption(f"Question {current_q + 1} of {total_questions}")
                
                # Show current anatomical region being evaluated
                question_type = question_data.get('type', 'specific')
                if question_type == 'screening':
                    st.info(f"🔍 **Starting New Region:** {question_data['category']} > {question_data.get('subcategory', '')}")
                else:
                    st.info(f"📋 **Current Region:** {question_data['category']} > {question_data.get('subcategory', '')} (In-depth)")
                
                # Question
                st.write(f"**Question:** {question_data['question']}")
                
                # Show category and subcategory (smaller, for reference)
                with st.expander("ℹ️ Question Details", expanded=False):
                    st.write(f"**Type:** {question_type.title()} Question")
                    st.write(f"**Category:** {question_data['category']}")
                    if question_data.get('subcategory'):
                        st.write(f"**Subcategory:** {question_data['subcategory']}")
                    if question_data.get('depends_on'):
                        st.write(f"**Related to:** {question_data['depends_on']}")
                
                # Show previous context for specific questions
                if question_data.get('type') == 'specific' and st.session_state.answers:
                    with st.expander("📝 Previous Findings (Context)", expanded=False):
                        for key, ans in st.session_state.answers.items():
                            if ans['answer'] == 'Yes' and ans['details']:
                                st.write(f"**{ans['question']}:** {ans['details']}")
                
                # Answer form
                with st.form("answer_form"):
                    answer = st.radio("Answer:", ["Yes", "No"], horizontal=True)
                    
                    # Always show details text area
                    if question_data.get('follow_up'):
                        st.info(f"**Follow-up Instructions:** {question_data['follow_up']}")
                    
                    # Show details text area for all questions
                    if answer == "Yes":
                        details = st.text_area(
                            "Provide details:", 
                            placeholder="Describe the finding, measurements, characteristics...",
                            help="Please provide detailed information about this finding",
                            key=f"details_{current_q}"
                        )
                    else:
                        # Still show text area but make it optional for "No" answers
                        details = st.text_area(
                            "Additional Comments (optional):", 
                            placeholder="Add any relevant notes...",
                            help="Optional: Add any comments if needed",
                            key=f"details_{current_q}"
                        )
                    
                    submitted = st.form_submit_button("Submit Answer", type="primary")
                    
                    if submitted:
                        # Validate that details are provided for "Yes" answers
                        if answer == "Yes" and not details.strip():
                            st.warning("⚠️ Please provide details for this finding before submitting.")
                        else:
                            # Store answer with details (strip whitespace)
                            answer_key = f"q_{current_q}"
                            st.session_state.answers[answer_key] = {
                                "question": question_data['question'],
                                "category": question_data['category'],
                                "subcategory": question_data.get('subcategory', 'General'),
                                "item": question_data.get('id', f"question_{current_q}"),
                                "answer": answer,
                                "details": details.strip(),  # Strip whitespace
                                "follow_up": question_data.get('follow_up', ''),
                                "type": question_data.get('type', 'specific')
                            }
                            
                            # If this is a screening question, store the answer for filtering specific questions
                            if question_data.get('type') == 'screening':
                                st.session_state.screening_answers[question_data.get('id', f"screening_{current_q}")] = answer
                            
                            # Move to next question
                            st.session_state.current_question += 1
                            st.rerun()
            else:
                st.success("🎉 All questions completed!")
                
                # Show summary
                positive_findings = []
                for key, answer_data in st.session_state.answers.items():
                    if answer_data['answer'] == 'Yes':
                        positive_findings.append({
                            "question": answer_data['question'],
                            "category": answer_data['category'],
                            "subcategory": answer_data['subcategory'],
                            "item": answer_data['item'],
                            "details": answer_data['details']
                        })
                
                st.subheader("Session Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Questions", len(st.session_state.answers))
                with col2:
                    st.metric("Positive Findings", len(positive_findings))
                
                if positive_findings:
                    st.subheader("Positive Findings")
                    for finding in positive_findings:
                        # Get the actual question text instead of just the item ID
                        question_text = finding.get('question', finding['item'])
                        st.write(f"**{finding['category']} > {finding['subcategory']}:** {question_text}")
                        if finding['details']:
                            st.write(f"*Details:* {finding['details']}")
                        else:
                            st.write(f"*Details:* ⚠️ (No details provided)")
                    
                    # Show JSON data for debugging
                    with st.expander("🔍 Debug: Raw Findings Data (JSON)", expanded=False):
                        st.json(positive_findings)
                        
                        # Add copy button for the JSON
                        st.code(json.dumps(positive_findings, indent=2), language="json")
                
                # Store findings for report generation
                st.session_state.findings = positive_findings
                
                if st.button("Generate Report", type="primary"):
                    st.session_state.ready_for_report = True
                    st.info("Go to 'Report Generation' page to create the final report.")

elif page == "Report Generation":
    st.header("📄 Report Generation")
    
    if 'case_metadata' not in st.session_state:
        st.warning("Please complete the case input and checklist process first.")
    elif 'findings' not in st.session_state:
        st.warning("Please complete the interactive checklist first.")
    else:
        case_metadata = st.session_state.case_metadata
        findings = st.session_state.findings
        
        st.subheader("Case Information")
        st.write(f"**Case ID:** {case_metadata['case_id']}")
        st.write(f"**Study:** {case_metadata['mod_study']}")
        st.write(f"**Findings:** {len(findings)} positive findings identified")
        
        # Debug: Show findings before generating report
        with st.expander("🔍 Debug: Findings Data", expanded=False):
            st.json(findings)
        
        if st.button("Generate Radiology Report", type="primary"):
            with st.spinner("Generating radiology report..."):
                try:
                    from src.report_generator import RadiologyReportGenerator
                    generator = RadiologyReportGenerator()
                    
                    # Debug: Check findings
                    st.write(f"Total findings passed to generator: {len(findings)}")
                    findings_with_details = [f for f in findings if f.get('details') and f.get('details').strip()]
                    st.write(f"Findings with details: {len(findings_with_details)}")
                    
                    report = generator.generate_complete_report(case_metadata, findings)
                    
                    st.session_state.generated_report = report
                    st.success("Report generated successfully!")
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Display generated report
        if 'generated_report' in st.session_state:
            report = st.session_state.generated_report
            
            st.subheader("Generated Radiology Report")
            
            # Display formatted report
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
            st.markdown(formatted_report)

elif page == "Report History":
    st.header("📚 Report History")
    st.write("Report history functionality will be implemented here.")

# Footer
st.markdown("---")
st.markdown("**CT Study Retrieval System** - Built with ChromaDB, OpenAI Embeddings, and Streamlit")
