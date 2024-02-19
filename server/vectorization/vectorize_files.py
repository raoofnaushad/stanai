from llama_index import SimpleDirectoryReader, StorageContext
from llama_index.indices.vector_store import VectorStoreIndex
from llama_index.vector_stores import PGVectorStore
from urllib.parse import quote_plus
import openai
from dotenv import load_dotenv
import os

from src import utils as U

load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]


def read_documents_from_directories(directories):
    """Read and aggregate documents from a list of directories."""
    all_documents = []
    for directory in directories:
        # Assuming SimpleDirectoryReader can be initialized with a directory path
        # and has a method load_data() that returns a list of documents
        documents = SimpleDirectoryReader(directory).load_data()
        all_documents.extend(documents)
    return all_documents


def to_vectorize_files():

    ## Step 1: Read Data from the files folder

    # Collect all subdirectories under "root folder"
    subdirectories = U.collect_subdirectories_with_files("./files")
    # Now, read documents from each directory and subdirectory
    documents = read_documents_from_directories(subdirectories)
    print("Total documents loaded:", len(documents))

    ## Step 2: Create a vector store and storage context
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

    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    ## Step 3 Creating an index and Storing the vector using Vector Store Index
    index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context, show_progress=True
    )


if __name__ == "__main__":
    to_vectorize_files()