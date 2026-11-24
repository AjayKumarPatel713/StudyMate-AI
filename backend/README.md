# StudyMate AI 🎓

### Personalized AI-Powered Learning Assistant

StudyMate AI is an AI-powered learning platform designed to help students study more effectively using their own notes, previous-year question papers, and intelligent AI assistance.

It combines **Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), document processing, and question analysis** to provide a personalized learning experience.

---

## 🚀 Key Features

### 1. AI Chat Assistant
- Ask questions and receive AI-generated answers.
- Uses uploaded study materials as context through RAG.
- Provides context-aware responses based on relevant document content.

### 2. Document Management
- Upload PDF, DOCX, PPTX, and TXT files.
- Extract text from uploaded documents.
- Supports OCR-based extraction for scanned PDFs.
- Automatically splits extracted content into smaller chunks.
- Generates embeddings and stores them in a FAISS vector index.
- Maintains document metadata in SQLite.

### 3. PYQ Analyzer
- Upload previous-year question papers in PDF format.
- Extract questions using Google's Gemini API.
- Automatically identify question topics.
- Store extracted questions in SQLite.
- Filter questions by subject, examination year, and topic.
- View topic-wise and year-wise question analytics.

### 4. PYQ Practice Mode
- Start practice sessions using subject, year, and topic filters.
- Attempt questions from stored previous-year papers.
- Save answers and track attempted questions.
- Review saved practice sessions.
- View previous practice session history.

> **Note:** Automatic answer checking and score calculation are planned for a future update because verified answer keys are not yet available.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend | FastAPI |
| Frontend | HTML, CSS, JavaScript |
| AI / LLM | Google Gemini API |
| RAG | Retrieval-Augmented Generation |
| Embeddings | Sentence Transformers |
| Embedding Model | all-MiniLM-L6-v2 |
| Vector Database | FAISS |
| Database | SQLite |
| Document Processing | PyMuPDF, python-docx, python-pptx |
| OCR | Tesseract OCR, Pytesseract |
| Data Validation | Pydantic |
| Testing | Pytest |
| Version Control | Git and GitHub |

---

## 🏗️ Project Architecture

```text
AI StudyMate/
│
├── backend/
│   ├── api/
│   │   ├── chat_routes.py
│   │   ├── document_routes.py
│   │   ├── pyq_routes.py
│   │   └── practice_routes.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── rag/
│   │   └── chunking.py
│   │
│   ├── schemas/
│   │   └── pyq_schema.py
│   │
│   ├── services/
│   │   ├── document_service.py
│   │   ├── embedding_service.py
│   │   ├── indexing_service.py
│   │   ├── llm_service.py
│   │   ├── pyq_service.py
│   │   ├── rag_service.py
│   │   └── vector_service.py
│   │
│   ├── config.py
│   └── main.py
│
├── frontend/
│   ├── assets/
│   ├── css/
│   ├── js/
│   └── index.html
│
├── data/
│   ├── vector_indexes/
│   └── pyq/
│
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

*The tree shows the main project structure; additional files may exist.*

---

## 🧠 How RAG Works in StudyMate AI

The application uses Retrieval-Augmented Generation to answer questions using uploaded study materials.

```text
      Upload Study Material
               |
               v
          Extract Text
               |
               v
        Split into Chunks
               |
               v
      Generate Embeddings
               |
               v
          Store in FAISS
               |
               v
        User Asks Question
               |
               v
     Retrieve Relevant Chunks
               |
               v
      Send Context to Gemini
               |
               v
         Generate Answer
```

This approach helps generate answers grounded in uploaded study material rather than relying only on general model knowledge.

---

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/AjayKumarPatel713/StudyMate-AI.git
cd StudyMate-AI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

Add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get an API key from [Google AI Studio](https://aistudio.google.com/).

**Important:** Never upload your actual `.env` file or API key to GitHub.

### 5. Install Tesseract OCR

Tesseract OCR is required for scanned PDF text extraction.

On Windows, install Tesseract OCR and ensure its executable path matches the configuration in:

`backend/services/document_service.py`

### 6. Start the Backend

From the project root, run:

```bash
uvicorn backend.main:app --reload
```

Backend URL: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

Health check: `http://127.0.0.1:8000/health`

### 7. Start the Frontend

Open the project in VS Code and use the **Live Server** extension to launch:

`frontend/index.html`

Frontend URL:

`http://127.0.0.1:5500/frontend/index.html`

Make sure the backend is running before using the frontend.

---

## 🔗 API Endpoints

### Chat API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | Ask questions to the AI assistant |

### Document API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/documents/upload` | Upload study documents |
| GET | `/api/documents` | Retrieve uploaded documents |

### PYQ Analyzer API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/pyq/upload` | Upload and analyze a question paper |
| GET | `/api/pyq/questions` | Retrieve questions |
| GET | `/api/pyq/analytics` | Get question analytics |
| DELETE | `/api/pyq/questions/{question_id}` | Delete a question |

**Question filtering supports:**
- `subject`
- `exam_year`
- `topic`

Example:

```text
/api/pyq/questions?subject=GATE&exam_year=2026&topic=Computer%20Networks
```

### Practice Mode API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/practice/start` | Start a practice session |
| GET | `/api/practice/history` | Retrieve practice history |
| GET | `/api/practice/{session_id}` | Retrieve session details |
| POST | `/api/practice/{session_id}/answer` | Save an answer |
| POST | `/api/practice/{session_id}/complete` | Complete a session |

---

## 🗄️ Database Structure

StudyMate AI uses SQLite for persistent data storage.

| Table | Purpose |
|---|---|
| `documents` | Stores uploaded document metadata |
| `pyq_questions` | Stores extracted previous-year questions |
| `practice_sessions` | Stores practice session information |
| `practice_answers` | Stores user responses |

FAISS stores vector embeddings separately for semantic document retrieval.

---

## 🧪 Running Tests

Run the test suite from the project root:

```bash
python -m pytest -v
```

---

## 🔮 Future Improvements

- Verified answer-key extraction and automatic answer evaluation.
- Practice performance analytics and scoring.
- Timed mock tests and customizable examinations.
- Hybrid search combining semantic and keyword retrieval.
- Retrieval-quality evaluation.
- More detailed AI-generated explanations.
- Personalized learning recommendations.
- Cloud deployment and production optimization.

---

## 📂 Project Repository

[**StudyMate AI — GitHub Repository**](https://github.com/AjayKumarPatel713/StudyMate-AI)

---

## 👨‍💻 Author

**Ajay Kumar Patel**

B.Tech — Computer Science and Engineering

---

<p align="center">
  <strong>StudyMate AI — Making personalized learning smarter with Artificial Intelligence.</strong>
</p>