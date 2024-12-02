from modal import Image, App, asgi_app, Secret
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from app.utils.rag import get_answer_and_docs, async_get_answer_and_docs
from app.utils.qdrant import upload_website_to_collection
from pydantic import BaseModel
from decouple import config
from fastapi.middleware.cors import CORSMiddleware
import json

app = App("rag-backend")

# app.image = Image.debian_slim().poetry_install_from_file("./requirement.txt")

app.image = Image.debian_slim().pip_install_from_requirements("./requirements.txt")


qdrant_api_key = config("QDRANT_API_KEY")
qdrant_url = config("QDRANT_URL")
openai_api_key = config("OPENAI_API_KEY")

print(qdrant_api_key, qdrant_url, openai_api_key)


@app.function(secrets=[Secret.from_dotenv()])
@asgi_app()
def endpoint():

    app = FastAPI(
        title="RAG API",

        description="A simple RAG API",
        version="0.1",
    )

    origins = [
        "http://localhost:3000",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    class Message(BaseModel):
        message: str

    @app.websocket('/async_chat')
    async def async_chat(websocket: WebSocket):
        await websocket.accept()
        while True:
            question = await websocket.receive_text()
            async for event in async_get_answer_and_docs(question):
                if event["event_type"] == "done":
                    await websocket.close()
                    return
                else:
                    await websocket.send_text(json.dumps(event))

    @app.post("/chat", description="Chat with the RAG API through this endpoint")
    def chat(message: Message):
        response = get_answer_and_docs(message.message)
        response_content = {
            "question": message.message,
            "answer": response["answer"],
            "documents": [doc.dict() for doc in response["context"]]
        }
        return JSONResponse(content=response_content, status_code=200)

    @app.post("/indexing", description="Index a website through this endpoint")
    def indexing(url: Message):
        try:
            response = upload_website_to_collection(url.message)
            return JSONResponse(content={"response": response}, status_code=200)

        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=400)

    return app
