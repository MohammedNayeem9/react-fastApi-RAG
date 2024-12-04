import os
import json
import tempfile
import multipart
from fastapi import FastAPI, WebSocket, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Environment management
from decouple import Config, RepositoryEnv

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


from app.utils.rag import get_answer_and_docs, async_get_answer_and_docs
from app.utils.qdrant import upload_website_to_collection


env_config = Config(RepositoryEnv("F:/Projects/react-fastApi-RAG/apps/backend/app/.env"))
QDRANT_API_KEY = env_config("QDRANT_API_KEY")
QDRANT_URL = env_config("QDRANT_URL")
OPENAI_API_KEY = env_config("OPENAI_API_KEY")


app = FastAPI(
    title="RAG API",
    description="Simple and robust RAG API for PDF processing and web content indexing",
    version="0.1"
)


origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/response models
class Message(BaseModel):
    message: str

# Root endpoint
@app.get("/", description="Root endpoint to check API health")
def read_root():
    return {"message": "Welcome to the RAG API! The server is running."}

# Chat endpoint
@app.post("/chat", description="Chat with the RAG API through this endpoint")
def chat(message: Message):
    try:
        response = get_answer_and_docs(message.message)
        response_content = {
            "question": message.message,
            "answer": response["answer"],
            "documents": [doc.dict() for doc in response["context"]],
        }
        return JSONResponse(content=response_content, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Website indexing endpoint
@app.post("/indexing", description="Index a website through this endpoint")
def indexing(url: Message):
    try:
        response = upload_website_to_collection(url.message)
        return JSONResponse(content={"response": response}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

# PDF processing endpoint
@app.post("/process_pdf", description="Process a PDF file and extract its contents")
async def process_pdf(file: UploadFile = File(...)):
    try:
        # Validate file type
        if file.content_type not in ['application/pdf', 'application/x-pdf']:
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        # Create a temporary file to save the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Load and split the PDF
        loader = PyPDFLoader(temp_file_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.split_documents(documents)

        # Prepare response
        response = [
            {
                "page_content": doc.page_content,
                "metadata": {
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page", 0),
                }
            }
            for doc in split_docs
        ]

        # Delete the temporary file
        os.unlink(temp_file_path)

        return {"status": "success", "total_chunks": len(response), "documents": response}

    except Exception as e:
        return JSONResponse(content={"error": f"Processing failed: {str(e)}"}, status_code=500)
try:
    import multipart
except ImportError:
    raise RuntimeError("python-multipart is not installed. Please install it with `pip install python-multipart`.")
