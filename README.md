# Git2Doc 📚

[![PyPI version](https://badge.fury.io/py/git2doc.svg)](https://pypi.org/project/git2doc/)

Git2Doc is a Python package that allows you to convert git repositories into documents. It is designed to help developers analyze and understand codebases by providing an easy way to extract and process text content from git repositories.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Example: Fetch and Load Repositories](#example-fetch-and-load-repositories)
  - [Example: Get Top Repositories](#example-get-top-repositories)
- [Contributing](#contributing)
- [License](#license)

## Installation

To install Git2Doc, simply run:

```bash
pip install git2doc
```

## Usage

### Example: Fetch and Load Repositories

```python
from git2doc.loader import pipeline_fetch_and_load

# Fetch and load the top 5 repositories created in the last 7 days
github_data = pipeline_fetch_and_load(n_repos=5, last_n_days=7)

# Print the metadata and documents for each repository
for repo_key, repo_data in github_data.items():
    print(f"Repository: {repo_key}")
    print("Metadata:")
    for key, value in repo_data["metadata"].items():
        print(f"  {key}: {value}")
    print("Documents:")
    for doc in repo_data["docs"]:
        print(f"  {doc.metadata['file_path']}: {doc.page_content[:50]}...")
```

### Example: Get Top Repositories

```python
from git2doc.loader import get_top_repos

# Get the top 5 Python repositories created in the last 7 days
top_repos = get_top_repos(n_repos=5, last_n_days=7, language="Python")

# Print the repository URLs
for repo in top_repos:
    print(repo["html_url"])
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## License

Git2Doc is released under the [MIT License](https://opensource.org/licenses/MIT).