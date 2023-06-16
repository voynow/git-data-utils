# Git2Vec

Git2Vec is a Python package for handling Git data. It provides functionality to load and process Git repositories, and supports concurrent file loading for improved performance. The package can be found on [PyPI](https://pypi.org/project/git2vec/).

## Installation

To install Git2Vec, run the following command:

```bash
pip install git2vec
```

## Setup

Before using Git2Vec, make sure to have the following dependencies installed:

- langchain
- pinecone-client
- tiktoken
- gitpython
- python-dotenv
- pandas

You can install them using the following command:

```bash
pip install -r requirements.txt
```

## Usage

### Loading Git Repositories

The main functionality of Git2Vec is provided by the `loader.py` module. Here's an example of how to use the `pull_code_from_repo` function to load a Git repository:

```python
from git2vec.loader import pull_code_from_repo

repo_url = "https://github.com/username/repo.git"
branch = "main"

repo_data = pull_code_from_repo(repo_url, branch)
```

### Getting Top Repositories

You can use the `get_top_repos` function to fetch the top repositories based on certain criteria:

```python
from git2vec.loader import get_top_repos

n_repos = 10
last_n_days = 30
language = "Python"
sort = "stars"
order = "desc"

top_repos = get_top_repos(n_repos, last_n_days, language, sort, order)
```

### Pipeline Fetch and Load

The `pipeline_fetch_and_load` function can be used to fetch and load repositories in a single step:

```python
from git2vec.loader import pipeline_fetch_and_load

n_repos = 10
last_n_days = 30
language = "Python"
sort = "stars"
order = "desc"

github_data = pipeline_fetch_and_load(n_repos, last_n_days, language, sort, order)
```

## Contributing

If you'd like to contribute to Git2Vec, feel free to fork the repository and submit a pull request. If you have any questions or issues, please open an issue on the GitHub repository.

## License

Git2Vec is released under the MIT License.