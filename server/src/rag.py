import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

from llama_index.vector_stores import PGVectorStore
from llama_index.indices.vector_store import VectorStoreIndex


def query_response(query):

    ## Step - 1: Setup the vector store and storage context
    encoded_password = quote_plus(os.environ["POSTGRES_PASSWORD"])
    vector_store = PGVectorStore.from_params(
        database=os.environ["POSTGRES_DB"],
        host=os.environ["POSTGRES_HOST"],
        password=encoded_password,
        port=os.environ["POSTGRES_PORT"],
        user=os.environ["POSTGRES_USER"],
        table_name=os.environ["POSTGRES_VECTOR_TABLE"],
        embed_dim=1536,  # openai embedding dimension
    )

    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    query_engine = index.as_query_engine()
    response = query_engine.query(f"{query}")
    return response
