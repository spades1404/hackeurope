# TunaTax MVP 

This is the backend for **TunaTax**, an agentic tax compliance autopilot for multinational businesses, built with Python, FastAPI, SQLite, and the `litellm` SDK.

## Setup Instructions

1. **Install Python Packages**:
   Ensure you have Python 3.11+ installed. Create a virtual environment (optional but recommended) and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   In the root directory, there is a `.env` file. You must add your Gemini API key to this file:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **Start the Backend**:
   Run the FastAPI server centrally from this root directory:
   ```bash
   uvicorn backend.main:app --reload
   ```
   The backend will start at `http://127.0.0.1:8000`. 
   
   To view the interactive Swagger API documentation, navigate to:
   `http://127.0.0.1:8000/docs`

## Features Implemented
- **Compliance Engine (`backend/compliance_engine.py`)**: Computes tax deadlines based on jurisdictions and company demographics against `data/tax_knowledge_base.json`.
- **Document Generator (`backend/document_generator.py`)**: Creates draft forms based on action configurations and financial data.
- **AI Agent (`backend/agent.py`)**: A chat integration using `google-genai` with function tools that trigger compliance lookups, doc generator, and Google Search.
- **PDF Exporter (`backend/pdf_export.py`)**: Uses `reportlab` to render document JSON into a structured, DRAFT-watermarked PDF.
- **Async Database (`backend/database.py`)**: Stores `companies`, `actions`, `documents`, and `chat_messages` using `aiosqlite`.
- **Main API (`backend/main.py`)**: All required endpoints integrated and auto-initializing the database.
