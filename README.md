# Git2Doc 📚
[![PyPI version](https://badge.fury.io/py/git2doc.svg)](https://badge.fury.io/py/git2doc)
[![GitHub stars](https://img.shields.io/github/stars/voynow/git2doc.svg)](https://github.com/voynow/git2doc/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/voynow/git2doc.svg)](https://github.com/voynow/git2doc/issues)

A Python package for converting git repositories into documents. Git2Doc is a powerful tool that allows you to extract and analyze code from GitHub repositories, making it easier to understand and work with large codebases.

## Why Git2Doc? 🚀

- Extract code from repositories with ease
- Analyze code in a structured manner
- Filter out unwanted file types
- Save extracted data in a convenient format (e.g., Parquet)

## Table of Contents 📑

- [Installation](#installation)
- [Usage](#usage)
  - [Fetching Repositories](#fetching-repositories)
  - [Loading Repository Data](#loading-repository-data)
  - [Writing Data to Parquet Files](#writing-data-to-parquet-files)
- [Badges](#badges)

## Installation 💻

```bash
pip install git2doc
```

## Usage 🛠

### Fetching Repositories

```python
from git2doc.loader import get_repos_orchestrator

repos = get_repos_orchestrator(
    n_repos=10,
    last_n_days=30,
    language="Python"
)
```

### Loading Repository Data

```python
from git2doc.loader import pull_code_from_repo

repo_data = pull_code_from_repo(
    repo="https://github.com/voynow/git2doc",
    branch="main",
    delete=True
)
```

### Writing Data to Parquet Files

```python
from git2doc.loader import pipeline_fetch_and_load

pipeline_fetch_and_load(
    n_repos=10,
    last_n_days=30,
    language="Python",
    write_batch_size=100
)
```