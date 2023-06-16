import concurrent.futures
from datetime import datetime, timedelta
import dotenv
from git import Blob
import os
import requests
from typing import Callable, List, Optional, Dict

from langchain.docstore.document import Document
from langchain.document_loaders.base import BaseLoader

dotenv.load_dotenv()
access_token = os.environ.get("GITHUB_ACCESS_TOKEN")

UNWANTED_TYPES = [
    ".ipynb",
    ".yaml",
    ".yml",
    ".json",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    "csv",
    ".txt",
]


class TurboGitLoader(BaseLoader):
    """
    Loads files from a Git repository into a list of documents in parallel.

    Credit to GPT4.
    """

    def __init__(
        self,
        repo_path: str,
        clone_url: Optional[str] = None,
        branch: Optional[str] = "main",
        file_filter: Optional[Callable[[str], bool]] = None,
    ):
        """Initializes the loader with the given parameters.

        Parameters:
            repo_path: The path to the repository.
            clone_url: The URL to clone the repository from, if it's not local.
            branch: The branch to load the files from.
            file_filter: A function to filter the files to load.
        """
        self.repo_path = repo_path
        self.clone_url = clone_url
        self.branch = branch
        self.file_filter = file_filter

    def _load_file(self, item) -> Optional[Document]:
        """Loads a single file from the repository.

        Parameters:
            item: The item to load.

        Returns:
            The document, or None if the file could not be loaded.
        """
        if not isinstance(item, Blob):
            return None

        file_path = os.path.join(self.repo_path, item.path)

        # uses filter to skip files
        if self.file_filter and not self.file_filter(file_path):
            return None

        rel_file_path = os.path.relpath(file_path, self.repo_path)
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                file_type = os.path.splitext(item.name)[1]

                # loads only text files
                try:
                    text_content = content.decode("utf-8")
                except UnicodeDecodeError:
                    return None

                metadata = {
                    "file_path": rel_file_path,
                    "file_name": item.name,
                    "file_type": file_type,
                }
                doc = Document(page_content=text_content, metadata=metadata)
                return doc
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def load(self) -> List[Document]:
        """Loads all files from the repository in parallel.

        Returns:
            The list of documents.
        """
        from git import Repo

        if not os.path.exists(self.repo_path) and self.clone_url is None:
            raise ValueError(f"Path {self.repo_path} does not exist")
        elif self.clone_url:
            if os.path.exists(self.repo_path):
                repo = Repo(self.repo_path)
                origin = repo.remote(name='origin')
                origin.pull()
            else:
                repo = Repo.clone_from(self.clone_url, self.repo_path)
                repo.git.checkout(self.branch)
        else:
            repo = Repo(self.repo_path)
            repo.git.checkout(self.branch)

        docs: List[Document] = []

        # Use a ThreadPoolExecutor to load files in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_item = {executor.submit(self._load_file, item): item for item in repo.tree().traverse()}
            for future in concurrent.futures.as_completed(future_to_item):
                doc = future.result()
                if doc is not None:
                    docs.append(doc)

        return docs
    

def docs_to_str(repo_data):
    """ Convert repo data to raw text """
    raw_repo = ""
    for item in repo_data:
        if item.page_content:
            raw_repo += f"{item.metadata['file_path']}:\n\n{item.page_content}\n\n"
    return raw_repo


def load(repo, branch="main", return_str=False):
    """ Load the git repo data using TurboGitLoader """
    folder_name = repo.split("/")[-1]
    filter_fn = lambda x: not any([x.endswith(t) for t in UNWANTED_TYPES])
    repo_path = f"./repodata/{folder_name}/"

    repo_docs = TurboGitLoader(
        clone_url=repo,
        repo_path=repo_path,
        branch=branch,
        file_filter=filter_fn,
    ).load()

    if return_str:
        return docs_to_str(repo_docs)
    else:
        return repo_docs


def flatten_dict(dd, separator="_", prefix=""):
    """
    Flattens a dictionary with nested structures

    :param dd: Input dictionary to be flattened
    :param separator: Separator for the keys in the flattened dictionary
    :param prefix: Prefix for the keys in the flattened dictionary
    :return: Flattened dictionary
    """
    return (
        {
            f"{prefix}{separator}{k}" if prefix else k: v
            for kk, vv in dd.items()
            for k, v in flatten_dict(vv, separator, kk).items()
        }
        if isinstance(dd, dict)
        else {prefix: dd}
    )


def get_trending_repos(
    n_repos: int = 10,
    last_n_days: int = 30,
    language: str = None,
    sort: str = "stars",
    order: str = "desc",
) -> Dict[str, Dict]:
    """
    Query for repos created in the last n days

    n_repos (int, optional): The number of repositories to return per page. Defaults to 10.
    last_n_days (int, optional): The number of past days to consider for trending repos. Defaults to 30.
    language (str, optional): The programming language to filter by. Defaults to None.
    sort (str, optional): The field to sort the results by. Defaults to "stars".
    order (str, optional): The ordering of the results. Defaults to "desc".
    """
    url = "https://api.github.com/search/repositories"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {access_token}",
    }

    query = f"language:{language}" if language else "is:public"
    date_since = (datetime.now() - timedelta(days=last_n_days)).strftime("%Y-%m-%d")
    query += f" created:>{date_since}"

    params = {"q": query, "sort": sort, "order": order, "per_page": n_repos}

    with requests.Session() as session:
        session.headers.update(headers)
        try:
            response = session.get(url, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print(f"HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            print(f"Unknown Error: {err}")

    return response.json()


# Mass repo data pipeline
def get_repo_data():
    pass

