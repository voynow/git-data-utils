# Git2Vec

Git2Vec is a text analysis tool that loads files from a Git repository, processes and embeds the text using OpenAI, and stores the embeddings in a Pinecone index for efficient retrieval and analysis.

## Dependencies

The following packages are required to use Git2Vec:

- langchain
- pinecone-client
- tiktoken
- gitpython
- turbo_docs
- toml
- setuptools
- wheel
- twine

Install them with the following commands:

```
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

## Repo Structure

- `exclude.toml`: Configuration file for excluding specific files for the `turbo_docs` package.
- `requirements.dev.txt`: Development dependencies.
- `requirements.txt`: Main dependencies.
- `git2vec/loader.py`: Functions for loading documents from a Git repository using the TurboGitLoader class.
- `git2vec/vectordb.py`: Functions for creating a Pinecone index, embedding documents and upserting them in the index.

## Usage

1. First, create a Pinecone API key and save it as the `PINECONE_API_KEY` environment variable in your `.env` file.
2. Create an OpenAI API key and save it as the `OPENAI_API_KEY` environment variable in your `.env` file.
3. Load the Git repository data:

```python
from git2vec.loader import load

repo_data = load(repo="https://github.com/your/repository.git", branch="main")
```

4. Create and insert embeddings into the Pinecone index:

```python
from git2vec.vectordb import create_vectorstore

create_vectorstore(repo_data)
```

5. Get the Pinecone vector store instance for text retrieval:

```python
from git2vec.vectordb import get_vectorstore

vector_store = get_vectorstore()
```

6. Use the vector store for information retrieval and analysis.