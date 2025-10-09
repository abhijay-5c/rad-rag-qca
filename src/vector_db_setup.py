import os
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
import glob

# Load environment variables
load_dotenv('pws.env')

class CTVectorDatabase:
    def __init__(self, persist_directory="./data/chroma_db"):
        """Initialize the vector database with ChromaDB"""
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="ct_studies",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        try:
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            text = "\n".join([page.page_content for page in pages])
            return text
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def get_study_name(self, pdf_path):
        """Extract study name from PDF filename"""
        filename = os.path.basename(pdf_path)
        study_name = os.path.splitext(filename)[0]  # Remove .pdf extension
        return study_name
    
    def process_pdf(self, pdf_path):
        """Process a single PDF file and return chunks with metadata"""
        print(f"Processing {pdf_path}...")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return []
        
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Get study name
        study_name = self.get_study_name(pdf_path)
        
        # Prepare documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "content": chunk,
                "metadata": {
                    "modality": "CT",
                    "study": study_name,
                    "chunk_id": i,
                    "source": pdf_path
                }
            }
            documents.append(doc)
        
        return documents
    
    def add_documents_to_collection(self, documents):
        """Add documents to ChromaDB collection"""
        if not documents:
            return
        
        # Prepare data for ChromaDB
        ids = []
        texts = []
        metadatas = []
        
        for i, doc in enumerate(documents):
            ids.append(f"{doc['metadata']['study']}_chunk_{doc['metadata']['chunk_id']}")
            texts.append(doc['content'])
            metadatas.append(doc['metadata'])
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        print(f"Added {len(documents)} chunks to collection")
    
    def process_all_pdfs(self, pdf_directory="./documents"):
        """Process all PDF files in the directory"""
        pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
        
        if not pdf_files:
            print("No PDF files found in the directory")
            return
        
        print(f"Found {len(pdf_files)} PDF files")
        
        for pdf_path in pdf_files:
            documents = self.process_pdf(pdf_path)
            self.add_documents_to_collection(documents)
        
        print("All PDFs processed successfully!")
    
    def query_collection(self, query, n_results=5, study_filter=None):
        """Query the collection for similar documents"""
        if study_filter:
            where_clause = {"study": study_filter}
        else:
            where_clause = None  # Search all studies
        
        if where_clause:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause
            )
        else:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
        
        return results
    
    def get_chunks_by_study_only(self, study_name, n_results=None):
        """Get all chunks for a specific study only (no text query)"""
        # Only filter by study name, not modality (to support CT, MRI, etc.)
        where_clause = {"study": study_name}
        
        if n_results:
            results = self.collection.get(
                where=where_clause,
                limit=n_results
            )
        else:
            results = self.collection.get(where=where_clause)
        
        return results
    
    def get_all_studies(self):
        """Get list of all studies in the collection"""
        results = self.collection.get()
        studies = set()
        for metadata in results['metadatas']:
            studies.add(metadata['study'])
        return list(studies)
    
    def get_collection_stats(self):
        """Get statistics about the collection"""
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

def main():
    """Main function to set up the vector database"""
    print("Setting up CT Vector Database...")
    
    # Initialize vector database
    vector_db = CTVectorDatabase()
    
    # Process all PDFs
    vector_db.process_all_pdfs()
    
    # Print statistics
    stats = vector_db.get_collection_stats()
    print("\nDatabase Statistics:")
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Total studies: {stats['total_studies']}")
    print("\nStudies and chunk counts:")
    for study, count in stats['studies'].items():
        print(f"  {study}: {count} chunks")
    
    print("\nVector database setup complete!")

if __name__ == "__main__":
    main()
