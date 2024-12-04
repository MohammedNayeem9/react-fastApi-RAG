from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_openai import ChatOpenAI  
from operator import itemgetter

from decouple import config
from .qdrant import vector_store, qdrant_search
from .openai_utils import stream_completion


model = ChatOpenAI(
    model_name="gpt-4o",
    api_key=config("OPENAI_API_KEY"),  
    temperature=0,
)


prompt_template = """
Answer the question based on the context, in a concise manner, in markdown and using bullet points where applicable.

Context: {context}
Question: {question}
Answer:
"""

prompt = ChatPromptTemplate.from_template(prompt_template)


retriever = vector_store.as_retriever(
    search_kwargs={
        "k": 4,  
    }
)

def create_chain():
    chain = (
        {
            "context": retriever,  
            "question": RunnablePassthrough(),
        }
        | RunnableParallel({
            "response": prompt | model,
            "context": itemgetter("context"),
        })
    )
    return chain

def get_answer_and_docs(question: str):
    try:
        chain = create_chain()
        response = chain.invoke(question)
        answer = response["response"].content
        context = response["context"]
        return {
            "answer": answer,
            "context": context
        }
    except Exception as e:
        return {
            "answer": f"Error retrieving answer: {str(e)}",
            "context": []
        }

async def async_get_answer_and_docs(question: str):
    try:
        
        docs = qdrant_search(query=question)
        
        
        docs_dict = [
            {
                "page_content": doc.payload.get('page_content', ''),
                "metadata": doc.payload.get('metadata', {})
            } for doc in docs
        ]
        
        
        yield {
            "event_type": "on_retriever_end",
            "content": docs_dict
        }

        
        async for chunk in stream_completion(question, docs_dict):
            yield {
                "event_type": "on_chat_model_stream",
                "content": chunk
            }

        
        yield {
            "event_type": "done"
        }
    
    except Exception as e:
        yield {
            "event_type": "error",
            "content": str(e)
        }
        yield {
            "event_type": "done"
        }