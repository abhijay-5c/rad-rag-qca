import streamlit as st
import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv
import pandas as pd
import json
from datetime import datetime
from checklist_generator import RadiologyChecklistGenerator, InteractiveQASystem
from report_generator import RadiologyReportGenerator, ReportDatabase

# Load environment variables
load_dotenv('pws.env')

class CTRetrievalUI:
    def __init__(self):
        """Initialize the retrieval UI"""
        self.persist_directory = "./data/chroma_db"
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_collection("ct_studies")
    
    def get_all_studies(self):
        """Get list of all studies in the collection"""
        try:
            results = self.collection.get()
            studies = set()
            for metadata in results['metadatas']:
                studies.add(metadata['study'])
            return sorted(list(studies))
        except Exception as e:
            st.error(f"Error retrieving studies: {str(e)}")
            return []
    
    def get_collection_stats(self):
        """Get statistics about the collection"""
        try:
            results = self.collection.get()
            total_chunks = len(results['ids'])
            
            studies = {}
            for metadata in results['metadatas']:
                study = metadata['study']
                if study not in studies:
                    studies[study] = 0
                studies[study] += 1
            
            return {
                "total_chunks": total_chunks,
                "total_studies": len(studies),
                "studies": studies
            }
        except Exception as e:
            st.error(f"Error getting collection stats: {str(e)}")
            return {"total_chunks": 0, "total_studies": 0, "studies": {}}
    
    def search_chunks(self, query, study_filter=None, n_results=10):
        """Search for chunks based on query"""
        try:
            if study_filter and study_filter != "All Studies":
                where_clause = {"$and": [{"modality": "CT"}, {"study": study_filter}]}
            else:
                where_clause = {"modality": "CT"}
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
            
            return results
        except Exception as e:
            st.error(f"Error searching chunks: {str(e)}")
            return None
    
    def search_by_study_name(self, study_name, n_results=10):
        """Search for chunks by study name only (no text query)"""
        try:
            where_clause = {"$and": [{"modality": "CT"}, {"study": study_name}]}
            
            results = self.collection.get(
                where=where_clause,
                limit=n_results
            )
            
            return results
        except Exception as e:
            st.error(f"Error searching by study name: {str(e)}")
            return None
    
    def get_chunks_by_study(self, study_name):
        """Get all chunks for a specific study"""
        try:
            results = self.collection.get(
                where={"$and": [{"modality": "CT"}, {"study": study_name}]}
            )
            return results
        except Exception as e:
            st.error(f"Error retrieving chunks for study {study_name}: {str(e)}")
            return None

def main():
    """Main Streamlit app"""
    st.set_page_config(
        page_title="CT Study Retrieval System",
        page_icon="🏥",
        layout="wide"
    )
    
    st.title("🏥 CT Study Retrieval System")
    st.markdown("Search and retrieve CT study chunks from the vector database")
    
    # Initialize the UI
    ui = CTRetrievalUI()
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Search", 
        "Browse by Study", 
        "Database Statistics",
        "Case Input",
        "Interactive Checklist",
        "Report Generation",
        "Report History"
    ])
    
    if page == "Search":
        st.header("🔍 Search CT Study Chunks")
        
        # Search mode selection
        search_mode = st.radio(
            "Choose search mode:",
            ["Search by Study Name", "Search by Content"],
            horizontal=True
        )
        
        studies = ui.get_all_studies()
        
        if search_mode == "Search by Study Name":
            st.subheader("📚 Search by Study Name")
            st.markdown("Select a study to view all its chunks:")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                selected_study = st.selectbox("Select CT Study:", studies)
            
            with col2:
                n_results = st.number_input("Max results:", min_value=1, max_value=100, value=20)
            
            if st.button("Get Study Chunks", type="primary"):
                with st.spinner(f"Retrieving chunks for {selected_study}..."):
                    results = ui.search_by_study_name(selected_study, n_results)
                    
                    if results and results['documents']:
                        st.success(f"Found {len(results['documents'])} chunks for {selected_study}")
                        
                        # Display results
                        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                            with st.expander(f"Chunk {metadata['chunk_id']} - {selected_study}"):
                                st.markdown("**Study:** " + metadata['study'])
                                st.markdown("**Modality:** " + metadata['modality'])
                                st.markdown("**Chunk ID:** " + str(metadata['chunk_id']))
                                st.markdown("**Content:**")
                                st.text(doc)
                    else:
                        st.warning(f"No chunks found for {selected_study}")
        
        else:  # Search by Content
            st.subheader("🔍 Search by Content")
            st.markdown("Search for specific content within CT studies:")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                query = st.text_input(
                    "Enter your search query:",
                    placeholder="e.g., chest findings, spine abnormalities, head trauma..."
                )
            
            with col2:
                n_results = st.number_input("Number of results:", min_value=1, max_value=50, value=10)
            
            # Study filter - now more prominent
            st.markdown("**Study Filter (Required):**")
            study_filter = st.selectbox(
                "Select specific study to search in:",
                ["All Studies"] + studies,
                help="Select a specific study to search only within that study's chunks"
            )
            
            if study_filter == "All Studies":
                st.warning("⚠️ Selecting 'All Studies' will search across all CT studies. For more precise results, select a specific study.")
            
            # Search button
            if st.button("Search Content", type="primary"):
                if query.strip():
                    with st.spinner("Searching..."):
                        results = ui.search_chunks(query, study_filter, n_results)
                        
                        if results and results['documents'][0]:
                            if study_filter != "All Studies":
                                st.success(f"Found {len(results['documents'][0])} results in {study_filter}")
                            else:
                                st.success(f"Found {len(results['documents'][0])} results across all studies")
                            
                            # Display results
                            for i, (doc, metadata, distance) in enumerate(zip(
                                results['documents'][0],
                                results['metadatas'][0],
                                results['distances'][0]
                            )):
                                with st.expander(f"Result {i+1} - {metadata['study']} (Chunk {metadata['chunk_id']}) - Similarity: {1-distance:.3f}"):
                                    st.markdown("**Study:** " + metadata['study'])
                                    st.markdown("**Modality:** " + metadata['modality'])
                                    st.markdown("**Chunk ID:** " + str(metadata['chunk_id']))
                                    st.markdown("**Content:**")
                                    st.text(doc)
                        else:
                            if study_filter != "All Studies":
                                st.warning(f"No results found for '{query}' in {study_filter}.")
                            else:
                                st.warning(f"No results found for '{query}' across all studies.")
                else:
                    st.warning("Please enter a search query.")
    
    elif page == "Browse by Study":
        st.header("📚 Browse CT Studies")
        
        studies = ui.get_all_studies()
        
        if studies:
            selected_study = st.selectbox("Select a study to browse:", studies)
            
            if st.button("Load Study Chunks", type="primary"):
                with st.spinner("Loading study chunks..."):
                    results = ui.get_chunks_by_study(selected_study)
                    
                    if results and results['documents']:
                        st.success(f"Found {len(results['documents'])} chunks for {selected_study}")
                        
                        # Display chunks
                        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                            with st.expander(f"Chunk {metadata['chunk_id']}"):
                                st.markdown("**Study:** " + metadata['study'])
                                st.markdown("**Modality:** " + metadata['modality'])
                                st.markdown("**Content:**")
                                st.text(doc)
                    else:
                        st.warning(f"No chunks found for {selected_study}")
        else:
            st.warning("No studies found in the database.")
    
    elif page == "Database Statistics":
        st.header("📊 Database Statistics")
        
        with st.spinner("Loading statistics..."):
            stats = ui.get_collection_stats()
            
            if stats['total_chunks'] > 0:
                # Overview metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Chunks", stats['total_chunks'])
                
                with col2:
                    st.metric("Total Studies", stats['total_studies'])
                
                with col3:
                    avg_chunks = stats['total_chunks'] / stats['total_studies'] if stats['total_studies'] > 0 else 0
                    st.metric("Avg Chunks per Study", f"{avg_chunks:.1f}")
                
                # Study breakdown
                st.subheader("Study Breakdown")
                
                # Create DataFrame for better display
                study_data = []
                for study, count in stats['studies'].items():
                    study_data.append({
                        'Study': study,
                        'Chunks': count,
                        'Percentage': f"{(count / stats['total_chunks']) * 100:.1f}%"
                    })
                
                df = pd.DataFrame(study_data)
                df = df.sort_values('Chunks', ascending=False)
                
                st.dataframe(df, use_container_width=True)
                
                # Visualization
                st.subheader("Chunks Distribution")
                st.bar_chart(df.set_index('Study')['Chunks'])
                
            else:
                st.warning("Database is empty. Please run the vector database setup first.")
    
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
                mod_study = st.selectbox("Study Type", ui.get_all_studies())
            
            case_id = st.text_input("Case ID (optional)", placeholder="Leave blank for auto-generation")
            
            submitted = st.form_submit_button("Generate Checklist", type="primary")
            
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
                    
                    # Store in session state
                    st.session_state.case_metadata = case_metadata
                    st.session_state.checklist_generated = False
                    st.session_state.qa_session = None
                    
                    st.success(f"Case metadata saved! Case ID: {case_id}")
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
            
            # Generate checklist if not already generated
            if not st.session_state.get('checklist_generated', False):
                if st.button("Generate Checklist", type="primary"):
                    with st.spinner("Generating checklist from study content..."):
                        generator = RadiologyChecklistGenerator()
                        checklist = generator.generate_checklist(case_metadata)
                        
                        if "error" in checklist:
                            st.error(f"Error generating checklist: {checklist['error']}")
                        else:
                            st.session_state.checklist = checklist
                            st.session_state.checklist_generated = True
                            st.session_state.qa_session = InteractiveQASystem()
                            st.success("Checklist generated successfully!")
                            st.rerun()
            else:
                # Display checklist and start Q&A
                checklist = st.session_state.checklist
                qa_session = st.session_state.qa_session
                
                # Show checklist structure
                with st.expander("📋 Generated Checklist Structure", expanded=False):
                    st.json(checklist)
                
                # Q&A Interface
                st.subheader("Interactive Q&A")
                
                # Get current question
                question_data = qa_session.get_next_question(checklist)
                
                if question_data.get("status") == "completed":
                    st.success("🎉 All questions completed!")
                    
                    # Show summary
                    summary = qa_session.get_session_summary()
                    st.subheader("Session Summary")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Questions", summary['total_questions'])
                    with col2:
                        st.metric("Positive Findings", len(summary['positive_findings']))
                    
                    if summary['positive_findings']:
                        st.subheader("Positive Findings")
                        for finding in summary['positive_findings']:
                            st.write(f"**{finding['category']} > {finding['subcategory']}:** {finding['item']}")
                            if finding['details']:
                                st.write(f"*Details:* {finding['details']}")
                    
                    # Store findings for report generation
                    st.session_state.findings = summary['positive_findings']
                    
                    if st.button("Generate Report", type="primary"):
                        st.session_state.ready_for_report = True
                        st.info("Go to 'Report Generation' page to create the final report.")
                
                elif question_data.get("status") == "question":
                    # Display current question
                    progress = question_data['progress']
                    
                    # Progress bar
                    total_progress = (progress['category'] - 1) / progress['total_categories']
                    st.progress(total_progress)
                    st.caption(f"Category {progress['category']}/{progress['total_categories']}: {question_data['category']}")
                    
                    # Question
                    st.write(f"**Question:** {question_data['question']}")
                    st.write(f"**Category:** {question_data['category']} > {question_data['subcategory']}")
                    
                    # Answer form
                    with st.form("answer_form"):
                        answer = st.radio("Answer:", ["Yes", "No"], horizontal=True)
                        details = st.text_area("Additional Details (if Yes):", placeholder="Describe the finding in detail...")
                        
                        submitted = st.form_submit_button("Submit Answer", type="primary")
                        
                        if submitted:
                            qa_session.set_current_question_data(question_data)
                            result = qa_session.process_answer(answer, details)
                            
                            if result.get("status") == "follow_up":
                                st.info("Follow-up questions generated based on your positive finding.")
                                # Handle follow-up questions here if needed
                            
                            st.rerun()
    
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
            
            if st.button("Generate Radiology Report", type="primary"):
                with st.spinner("Generating radiology report..."):
                    generator = RadiologyReportGenerator()
                    report = generator.generate_complete_report(case_metadata, findings)
                    
                    # Save report
                    db = ReportDatabase()
                    db.save_report(report)
                    
                    st.session_state.generated_report = report
                    st.success("Report generated successfully!")
            
            # Display generated report
            if 'generated_report' in st.session_state:
                report = st.session_state.generated_report
                
                st.subheader("Generated Radiology Report")
                
                # Display formatted report
                formatted_report = generator.format_report_for_display(report)
                st.markdown(formatted_report)
                
                # Download button
                st.download_button(
                    label="Download Report as Text",
                    data=formatted_report,
                    file_name=f"report_{report['case_id']}.txt",
                    mime="text/plain"
                )
                
                # Save to database
                if st.button("Save Report to Database"):
                    db = ReportDatabase()
                    if db.save_report(report):
                        st.success("Report saved to database!")
                    else:
                        st.error("Error saving report to database.")
    
    elif page == "Report History":
        st.header("📚 Report History")
        
        db = ReportDatabase()
        reports = db.get_all_reports()
        
        if not reports:
            st.info("No reports found in the database.")
        else:
            st.write(f"Found {len(reports)} reports in the database.")
            
            # Display reports in a table
            report_data = []
            for report in reports:
                report_data.append({
                    "Case ID": report['case_id'],
                    "Date": report['date'],
                    "Age": report['patient_info']['age'],
                    "Gender": report['patient_info']['gender'],
                    "Study": report['study_type'],
                    "Findings": len(report.get('findings', []))
                })
            
            df = pd.DataFrame(report_data)
            st.dataframe(df, use_container_width=True)
            
            # Select report to view
            selected_case_id = st.selectbox("Select a report to view:", [r['case_id'] for r in reports])
            
            if selected_case_id:
                selected_report = db.get_report(selected_case_id)
                if selected_report:
                    st.subheader(f"Report: {selected_case_id}")
                    
                    formatted_report = generator.format_report_for_display(selected_report)
                    st.markdown(formatted_report)
    
    # Footer
    st.markdown("---")
    st.markdown("**CT Study Retrieval System** - Built with ChromaDB, OpenAI Embeddings, and Streamlit")

if __name__ == "__main__":
    main()
