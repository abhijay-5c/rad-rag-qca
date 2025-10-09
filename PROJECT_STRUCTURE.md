# Project Structure

This document describes the organized structure of the RAG-based Junior Radiology QC Report system.

## Directory Structure

```
another-try/
├── config/                 # Configuration files
│   └── prompts.py         # Centralized LLM prompts
│
├── documents/             # PDF documents for RAG
│   ├── ct_chest.pdf
│   ├── ct_head.pdf
│   ├── ct_lumbar_spine.pdf
│   ├── ct_cervical_spine.pdf
│   ├── ct_thoracic_spine.pdf
│   ├── ct_soft_tissue_neck.pdf
│   └── ct_temporal_bone.pdf
│
├── src/                   # Source code
│   ├── checklist_generator.py      # Checklist generation logic
│   ├── report_generator.py         # Report generation logic
│   ├── vector_db_setup.py          # Vector database setup
│   ├── ct_retrieval_ui.py          # Retrieval UI
│   ├── demo_complete_workflow.py   # Demo workflow
│   ├── run_system.py               # System runner
│   ├── simple_qa_system.py         # Simple Q&A system
│   └── test_ui.py                  # UI tests
│
├── ui/                    # User interface
│   └── main.py           # Main Streamlit UI (formerly ct_ui_new.py)
│
├── data/                  # Generated data and databases
│   ├── chroma_db/        # Vector database
│   ├── reports.db        # Reports database
│   ├── *.json            # JSON data files
│   └── *.txt             # Text files
│
├── .gitignore            # Git ignore rules
├── pws.env               # Environment variables (API keys, etc.)
├── requirements.txt      # Python dependencies
├── README.md             # Project README
├── SIMPLIFIED_FLOW.md    # Simplified workflow documentation
├── SYSTEM_OVERVIEW.md    # System overview
└── PROJECT_STRUCTURE.md  # This file
```

## Key Files

### Configuration
- **`config/prompts.py`**: Centralized location for all LLM prompts used throughout the system
  - Checklist generation prompts
  - Question generation prompts
  - Report generation prompts (observations, impressions)
  - Fallback questions
  - Technique templates

### Source Code
- **`src/vector_db_setup.py`**: Sets up ChromaDB vector database from PDF documents
- **`src/checklist_generator.py`**: Generates checklists from RAG content
- **`src/report_generator.py`**: Generates radiology reports from findings
- **`src/run_system.py`**: Main system orchestrator

### User Interface
- **`ui/main.py`**: Main Streamlit application with:
  - Case input
  - Interactive checklist
  - Report generation
  - Report history

### Documents
- **`documents/*.pdf`**: CT imaging protocol PDFs used for RAG

### Data
- **`data/chroma_db/`**: Vector database storage
- **`data/reports.db`**: SQLite database for storing generated reports
- **`data/*.json`**: Case data and test files

## Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   - Copy `pws.env.example` to `pws.env` (if example exists)
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

4. Initialize vector database:
   ```bash
   cd src
   python vector_db_setup.py
   ```

5. Run the application:
   ```bash
   cd ..
   streamlit run ui/main.py
   ```

## Import Paths

With the new structure, imports should be:

```python
# For prompts
from config.prompts import CHECKLIST_SYSTEM_PROMPT, TECHNIQUE_TEMPLATES

# For modules (from src directory)
from vector_db_setup import CTVectorDatabase
from checklist_generator import RadiologyChecklistGenerator
from report_generator import RadiologyReportGenerator
```

## Benefits of New Structure

1. **Organized Files**: Clear separation of concerns (config, source, UI, data, documents)
2. **Centralized Prompts**: All prompts in one place for easy maintenance and updates
3. **Easier Navigation**: Developers can quickly find what they need
4. **Better Git Management**: Proper .gitignore for sensitive files and generated data
5. **Scalability**: Easy to add new modules, prompts, or document types

## Adding New Features

### Adding a New Prompt
1. Edit `config/prompts.py`
2. Add your prompt as a constant
3. Import it in the file where it's needed

### Adding a New Document Type
1. Add PDF to `documents/` folder
2. Run `python src/vector_db_setup.py` to reindex
3. Update technique templates in `config/prompts.py` if needed

### Adding a New Module
1. Create module in `src/` directory
2. Import necessary prompts from `config.prompts`
3. Update documentation
