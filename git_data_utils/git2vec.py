""" Retrieval Augmented Generation (RAG) using Langchain, Pinecone, and OpenAI 
"""

from concurrent.futures import ThreadPoolExecutor
import dotenv
from itertools import chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
import os
import pinecone
import tiktoken
from tqdm.auto import tqdm
from uuid import uuid4

dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

VECTOR_EMBEDDING_DIM = 1536
UPSERT_BATCH_SIZE = 200
INDEX_NAME = "testindex"


def get_text_splitter():
    """ document splitter function
    """
    tokenizer = tiktoken.get_encoding('cl100k_base')
    def tiktoken_len(text):
        tokens = tokenizer.encode(
            text,
            disallowed_special=()
        )
        return len(tokens)

    return RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=20,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )


def get_openai_embeddings():
    """ OpenAI Embeddings
    """
    return OpenAIEmbeddings(
        model='text-embedding-ada-002',
        openai_api_key=OPENAI_API_KEY,
    )


def pinecone_init(index=None):
    """ Initialize Pinecone database, Optionally create index
    """
    pinecone.init(
        api_key=PINECONE_API_KEY, 
        environment="us-west1-gcp-free"
    )

    if index:
        if index in pinecone.list_indexes():
            print(f"Clearing index {index} from previous runs...")
            pinecone.delete_index(index)
        else:
            print(f"Creating index {index}...")
            
        pinecone.create_index(
            name=index,
            metric='dotproduct',
            dimension=VECTOR_EMBEDDING_DIM,
        )

    return pinecone


def upsert_batch(index, batch):
    """ Upsert batch into Pinecone index
    """
    index.upsert(vectors=batch)


def process_data(record, embed, text_splitter):
    """ Process data into chunks and embed them
    """
    metadata = {
        'filename': record.metadata['file_name'],
        'filepath': record.metadata['file_path']
    }
    record_texts = text_splitter.split_text(record.page_content)
    texts_and_metadatas = [
        (text, {"chunk": j, "text": text, **metadata})
        for j, text in enumerate(record_texts)
    ]
    ids = [str(uuid4()) for _ in range(len(texts_and_metadatas))]
    embeds = embed.embed_documents([text for text, _ in texts_and_metadatas])
    return list(zip(ids, embeds, [metadata for _, metadata in texts_and_metadatas]))


def embed_and_upsert(data, index, embed):
    """ Embed and upsert data into Pinecone index
    """
    text_splitter = get_text_splitter()

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(chain.from_iterable(
            executor.map(process_data, data, [embed]*len(data), [text_splitter]*len(data))
        ))
        batches = [results[i:i + UPSERT_BATCH_SIZE] for i in range(0, len(results), UPSERT_BATCH_SIZE)]
        list(executor.map(upsert_batch, [index]*len(batches), batches))

    index_stats = index.describe_index_stats()
    print(f"Done!\n\ndescribe_index_stats:\n{index_stats}")


def create_vectorstore(repo):
    """ Create and return vectorstore
    """
    data = git_load_wrapper(repo)
    embed = get_openai_embeddings()

    pinecone = pinecone_init(INDEX_NAME)
    index = pinecone.Index(INDEX_NAME)

    embed_and_upsert(
        data=data, index=index, embed=embed
    )


def get_vectorstore():
    """Get vectorstore from Pinecone index"""

    pinecone = pinecone_init()
    embed = get_openai_embeddings()
    index = pinecone.Index(INDEX_NAME)

    vectorstore = Pinecone(
        index, embed.embed_query, "text"
    )
    return vectorstore
