from langchain_community.vectorstores import Qdrant
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import WebBaseLoader
from langchain_qdrant import Qdrant

from qdrant_client import QdrantClient, models
from .openai_utils import get_embedding
from decouple import config

# Load configuration for Qdrant
qdrant_api_key = config("QDRANT_API_KEY")
qdrant_url = config("QDRANT_URL")
collection_name = "Websites"


client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key
)


vector_store = Qdrant(
    client=client,
    collection_name=collection_name,
    embeddings=OpenAIEmbeddings(
        openai_api_key=config("OPENAI_API_KEY")  
    )
)


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=20,
    length_function=len
)


def create_collection(collection_name: str):
    """
    Create a new collection in Qdrant with the given name.
    """
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=1536,  # Vector size for OpenAI embeddings
            distance=models.Distance.COSINE  # Distance metric for similarity
        )
    )
    print(f"Collection '{collection_name}' created successfully.")


def upload_website_to_collection(url: str):
    """
    Upload content from a website to the specified Qdrant collection.

    Parameters:
        url (str): The website URL to fetch and process documents from.
    """
    # Check if the collection exists, create it if not
    if not client.collection_exists(collection_name=collection_name):
        create_collection(collection_name)

    # Load and split website content
    loader = WebBaseLoader(url)
    docs = loader.load_and_split(text_splitter)
    for doc in docs:
        doc.metadata = {"source_url": url}

    # Add documents to the Qdrant vector store
    vector_store.add_documents(docs)
    print(f"Successfully uploaded {len(docs)} documents to collection '{collection_name}' from '{url}'.")
    return f"Uploaded {len(docs)} documents."


def qdrant_search(query: str):
    """
    Perform a vector search in Qdrant based on the given query.

    Parameters:
        query (str): The query text for searching relevant documents.

    Returns:
        List of documents matching the query.
    """
    # Get query embedding
    vector_search = get_embedding(query)
    # Search the collection
    docs = client.search(
        collection_name=collection_name,
        query_vector=vector_search,
        limit=4
    )
    return docs
