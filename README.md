# Git2Vec Repo

Git2Vec is a Python module that allows you to load text files from a Git repository and create a searchable vector database using Langchain, Pinecone, and OpenAI.

## Installation

Install from https://pypi.org/project/git2vec/ using pip

```bash
pip install git2vec
```

If cloned, you will need to install the following packages:

```bash
pip install -r requirements.txt
```

If you are a developer, you will need to install the development requirements:

```bash
pip install -r requirements.dev.txt
```

## Usage

### Loading a Git repository

To load a Git repository, use the `git2vec.loader.load()` function:

```python
from git2vec import loader

repo_name = "https://github.com/voynow/turbo-docs"

# Returns a list of Document objects
repo_data = loader.load(repo_name)

# Or return a string of all the raw text
raw_repo = loader.load(repo_name, return_str=True)
```

### Creating and managing a vector database

To create a vector database from the loaded Git repository, use the following functions:

```python
from git2vec import vectordb

# Create a vector store from the Git repo
vectorstore = vectordb.create_vectorstore(repo_name)

# Retrieve the vector store from Pinecone index
vectorstore = vectordb.get_vectorstore()
```

## Modules

### loader.py

The `loader.py` module contains the `TurboGitLoader` class which can be used to load text files from a Git repository. The `load()` function takes a repository URL and returns a list of `Document` objects or a string containing all the raw text.

### vectordb.py

The `vectordb.py` module provides functions to create and manage a vector database using Langchain, Pinecone, and OpenAI. It contains functions for initializing Pinecone, upserting data, processing data, embedding and upserting, creating a vectorstore, and retrieving a vectorstore.

## Contributing

If you find any issues or have any suggestions, feel free to open an issue or submit a pull request. We welcome any contributions!

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).