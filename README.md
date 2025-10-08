# CT Study Retrieval System

A vector database system for searching and retrieving CT study chunks using ChromaDB, OpenAI embeddings, and recursive text splitting.

## Features

- **Vector Database**: ChromaDB with OpenAI text-embedding-3-small embeddings
- **Text Chunking**: Recursive text splitting with 1000 character chunks and 200 character overlap
- **Metadata**: Each chunk includes modality (CT) and study name (from PDF filename)
- **Web UI**: Streamlit interface for searching and browsing CT studies
- **Search**: Semantic search across all CT studies or filter by specific study

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Make sure your `pws.env` file contains your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run the System

```bash
# Set up the vector database and process PDFs
python run_system.py

# Start the web UI
streamlit run ct_retrieval_ui.py
```

## Usage

### Web Interface

The Streamlit UI provides three main pages:

1. **Search**: Search for specific content across all CT studies
2. **Browse by Study**: View all chunks for a specific CT study
3. **Database Statistics**: View overview of the database

### Programmatic Usage

```python
from vector_db_setup import CTVectorDatabase

# Initialize database
vector_db = CTVectorDatabase()

# Search for chunks
results = vector_db.query_collection("chest findings", n_results=5)

# Get all studies
studies = vector_db.get_all_studies()

# Get statistics
stats = vector_db.get_collection_stats()
```

## File Structure

```
├── requirements.txt          # Python dependencies
├── vector_db_setup.py       # Vector database setup and management
├── ct_retrieval_ui.py       # Streamlit web interface
├── run_system.py            # Main setup and test script
├── pws.env                  # Environment variables (API keys)
├── chroma_db/               # ChromaDB persistent storage
└── *.pdf                    # CT study PDF files
```

## PDF Processing

The system automatically processes all PDF files in the current directory:

- **Text Extraction**: Uses PyPDF2 to extract text from PDFs
- **Chunking**: Recursive text splitting with configurable parameters
- **Metadata**: Each chunk tagged with:
  - `modality`: "CT"
  - `study`: PDF filename (without extension)
  - `chunk_id`: Sequential chunk number
  - `source`: Full PDF file path

## Search Capabilities

- **Semantic Search**: Find relevant content using natural language queries
- **Study Filtering**: Filter results by specific CT study
- **Similarity Scoring**: Results ranked by semantic similarity
- **Metadata Display**: View study name, chunk ID, and content for each result

## Example Queries

- "chest findings"
- "spine abnormalities"
- "head trauma"
- "neck soft tissue"
- "cervical spine"
- "temporal bone"

## Configuration

### Text Splitting Parameters

In `vector_db_setup.py`, you can modify:

```python
self.text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # Size of each chunk
    chunk_overlap=200,      # Overlap between chunks
    length_function=len,
    separators=["\n\n", "\n", " ", ""]
)
```

### Search Parameters

- `n_results`: Number of results to return (default: 10)
- `study_filter`: Filter by specific study name
- `where_clause`: Additional metadata filters

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**: Make sure your API key is correctly set in `pws.env`
2. **PDF Processing Error**: Check that PDF files are readable and not corrupted
3. **ChromaDB Error**: Delete the `chroma_db` folder and re-run setup
4. **Import Errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`

### Logs

The system provides detailed logging during setup and processing. Check the console output for any error messages.

## Performance

- **Embedding Model**: text-embedding-3-small (fast and cost-effective)
- **Chunk Size**: 1000 characters (good balance of context and searchability)
- **Overlap**: 200 characters (ensures continuity across chunks)
- **Storage**: Persistent ChromaDB storage for fast retrieval
