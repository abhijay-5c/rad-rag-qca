#!/usr/bin/env python3
"""
Main script to run the CT Study Retrieval System
"""

import os
import sys
from vector_db_setup import CTVectorDatabase

def setup_database():
    """Set up the vector database"""
    print("🚀 Setting up CT Vector Database...")
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please make sure your pws.env file contains the OpenAI API key.")
        return False
    
    try:
        # Initialize and process
        vector_db = CTVectorDatabase()
        # Use the correct PDF directory path
        pdf_dir = "./rad-rag-qca/documents" if os.path.exists("./rad-rag-qca/documents") else "./documents"
        vector_db.process_all_pdfs(pdf_directory=pdf_dir)
        
        # Print statistics
        stats = vector_db.get_collection_stats()
        print("\n✅ Database Statistics:")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Total studies: {stats['total_studies']}")
        print("\n📚 Studies and chunk counts:")
        for study, count in stats['studies'].items():
            print(f"   {study}: {count} chunks")
        
        print("\n🎉 Vector database setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        return False

def test_queries():
    """Test some sample queries"""
    print("\n🔍 Testing sample queries...")
    
    try:
        vector_db = CTVectorDatabase()
        
        # Test study-specific queries
        print("\n📚 Testing study-specific searches:")
        test_studies = ["ct_chest", "ct_head", "ct_lumbar_spine"]
        
        for study in test_studies:
            print(f"\n📝 Study: '{study}'")
            results = vector_db.get_chunks_by_study_only(study, n_results=3)
            
            if results and results['documents']:
                print(f"   Found {len(results['documents'])} chunks:")
                for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                    print(f"   {i+1}. {metadata['study']} (Chunk {metadata['chunk_id']})")
                    print(f"      Preview: {doc[:100]}...")
            else:
                print("   No chunks found")
        
        # Test content queries with study filter
        print("\n🔍 Testing content searches with study filter:")
        test_queries = [
            ("chest findings", "ct_chest"),
            ("spine abnormalities", "ct_lumbar_spine"), 
            ("head trauma", "ct_head"),
            ("neck soft tissue", "ct_soft_tissue_neck")
        ]
        
        for query, study_filter in test_queries:
            print(f"\n📝 Query: '{query}' in {study_filter}")
            results = vector_db.query_collection(query, n_results=3, study_filter=study_filter)
            
            if results and results['documents'][0]:
                print(f"   Found {len(results['documents'][0])} results:")
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    print(f"   {i+1}. {metadata['study']} (Chunk {metadata['chunk_id']})")
                    print(f"      Preview: {doc[:100]}...")
            else:
                print("   No results found")
        
        print("\n✅ Query testing complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing queries: {str(e)}")
        return False

def main():
    """Main function"""
    print("🏥 CT Study Retrieval System")
    print("=" * 50)
    
    # Check if database exists
    if os.path.exists("./chroma_db"):
        print("📁 Existing database found.")
        choice = input("Do you want to rebuild the database? (y/n): ").lower().strip()
        if choice == 'y':
            import shutil
            shutil.rmtree("./chroma_db")
            print("🗑️  Removed existing database.")
        else:
            print("📖 Using existing database.")
    
    # Setup database
    if setup_database():
        # Test queries
        test_queries()
        
        print("\n" + "=" * 50)
        print("🎯 System is ready!")
        print("\nTo start the UI, run:")
        print("   streamlit run ct_retrieval_ui.py")
        print("\nOr to run setup again:")
        print("   python run_system.py")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
