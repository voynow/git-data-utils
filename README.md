# git2doc 📚

A powerful Python library for converting git repositories into documents. git2doc allows you to extract and analyze code from GitHub repositories, making it easier to understand and work with large codebases.

## Why git2doc? 🚀

Working with large repositories can be overwhelming, especially when trying to understand the structure and content of the code. git2doc simplifies this process by converting repositories into documents, allowing you to easily search, analyze, and understand the codebase.

## Table of Contents 📖

- [Installation](#installation)
- [Usage](#usage)
  - [Fetching Repositories](#fetching-repositories)
  - [Loading Repository Data](#loading-repository-data)
  - [Writing Data to Parquet Files](#writing-data-to-parquet-files)
- [Badges](#badges)
- [Contributing](#contributing)
- [License](#license)

## Installation 💻

```bash
pip install git2doc
```

## Usage 🛠️

### Fetching Repositories

```python
from git2doc import get_repos_orchestrator

repos = get_repos_orchestrator(
    n_repos=10,
    last_n_days=30,
    language="Python"
)
```

### Loading Repository Data

```python
from git2doc import pull_code_from_repo

repo_data = pull_code_from_repo(
    repo="https://github.com/voynow/git2doc",
    branch="main"
)
```

### Writing Data to Parquet Files

```python
from git2doc import pipeline_fetch_and_load

pipeline_fetch_and_load(
    n_repos=1000,
    last_n_days=365,
    language="Python",
    write_batch_size=100,
    delete=True,
)
```

## Badges 🏅

[![PyPI version](https://badge.fury.io/py/git2doc.svg)](https://badge.fury.io/py/git2doc)
[![GitHub stars](https://img.shields.io/github/stars/voynow/git2doc)](https://github.com/voynow/git2doc/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/voynow/git2doc)](https://github.com/voynow/git2doc/network)
[![GitHub issues](https://img.shields.io/github/issues/voynow/git2doc)](https://github.com/voynow/git2doc/issues)

## Contributing 🤝

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License 📄

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.