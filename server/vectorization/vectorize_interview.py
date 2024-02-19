from llama_index import SimpleDirectoryReader, StorageContext
from llama_index.indices.vector_store import VectorStoreIndex
from llama_index.vector_stores import PGVectorStore
from urllib.parse import quote_plus
import openai
from dotenv import load_dotenv
import os

from llama_index import download_loader

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]


def to_vectorize_interview(interview_id, table_name='interviewboard'):

    encoded_password = quote_plus(os.environ["POSTGRES_PASSWORD"])

    ## Step 1: Read interview minutes from postgresdb
    DatabaseReader = download_loader('DatabaseReader')

    reader = DatabaseReader(
        scheme = "postgresql", # Database Scheme
        host = os.environ["POSTGRES_HOST"],
        port = os.environ["POSTGRES_PORT"],
        user = os.environ["POSTGRES_USER"],
        password = encoded_password,
        dbname = os.environ["POSTGRES_DB"],
    )

    query = f"""
            SELECT meeting_summary
            FROM {table_name}
            WHERE id = {interview_id}
            """

    documents = reader.load_data(query=query)

    ## Step 2: Create a vector store and storage context
    vector_store = PGVectorStore.from_params(
        database=os.environ["POSTGRES_DB"],
        host=os.environ["POSTGRES_HOST"],
        password=encoded_password,
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        table_name=os.environ["POSTGRES_VECTOR_TABLE"],
        embed_dim=1536,  # openai embedding dimension
    )

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    ## Step 3 Creating an index and Storing the vector using Vector Store Index
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, show_progress=True
    )

    return index




if __name__ == "__main__":
    id = 13
    to_vectorize_interview(id)