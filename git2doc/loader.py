import concurrent.futures
from datetime import datetime, timedelta
import dotenv
import gc
from git import Blob, Repo
from git.exc import InvalidGitRepositoryError
import os
from pathlib import Path
import requests
import shutil
import stat
from typing import Callable, List, Optional, Dict

from langchain.docstore.document import Document


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
    ".csv",
    ".txt",
    ".jsonl",
    ".struct",
    ".map",
    ".obj",
    ".cleaned",
    ".dict",
    ".GIF",
]
REPODATA_FOLDER = "./repodata/"


def load_file(item, output_path) -> Optional[Document]:
    """
    Loads a single file from the repository.

    :param item: The file to load.
    :return: The document or None if the file should be skipped.
    """
    if not isinstance(item, Blob):
        return None

    file_path = os.path.join(output_path, item.path)

    if any([file_path.endswith(t) for t in UNWANTED_TYPES]):
        return None

    rel_file_path = os.path.relpath(file_path, output_path)
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            file_type = os.path.splitext(item.name)[1]

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


def load_concurrently(repo, output_path) -> List[Document]:
    """
    Loads all files from the repository in parallel.

    :return: A list of documents
    """

    docs: List[Document] = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_item = {
            executor.submit(load_file, item, output_path): item
            for item in repo.tree().traverse()
        }
        for future in concurrent.futures.as_completed(future_to_item):
            doc = future.result()
            if doc is not None:
                docs.append(doc)
        executor.shutdown(wait=True)

    return docs


def git_pull(clone_url, branch, output_path):
    """
    Pull the repo if it exists, otherwise clone it

    :param output_path: local path to output
    :param clone_url: URL to the repo
    :param branch: default branch name
    :return: Repo object
    """
    if os.path.exists(output_path):
        repo = Repo(output_path)
        origin = repo.remote(name="origin")
        origin.pull()
    else:
        repo = Repo.clone_from(
            clone_url,
            output_path,
            allow_unsafe_options=True,
            multi_options=["--config", "lfs.fetchexclude=*"],
        )
        repo.git.checkout(branch)
    return repo


def docs_to_str(repo_data):
    """Convert repo data to raw text"""
    raw_repo = ""
    for item in repo_data:
        if item.page_content:
            raw_repo += f"{item.metadata['file_path']}:\n\n{item.page_content}\n\n"
    return raw_repo


def readonly_to_writable(fn, file, err):
    """Exception handler for OS error on rmtree"""
    if Path(file).suffix in [".idx", ".pack"] and "PermissionError" == err[0].__name__:
        os.chmod(file, stat.S_IWRITE)
        fn(file)


def pull_code_from_repo(repo, branch="main", delete=False):
    """
    Load the git repo data using TurboGitLoader

    :param repo: URL to the repo
    :param branch: default branch name
    :param return_str: return raw text or not
    """
    folder_name = "/".join(repo.split("/")[3:5])
    output_path = f"{REPODATA_FOLDER}{folder_name}/"

    # git pull, load, and delete repo
    repo = git_pull(repo, branch, output_path)
    repo_docs = load_concurrently(repo, output_path)

    if delete:
        shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)

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


def get_access_token():
    """Can be stored in a .env file or as an environment variable"""
    dotenv.load_dotenv()
    access_token = os.getenv("GITHUB_ACCESS_TOKEN")
    if not access_token:
        raise ValueError(
            "ACCESS_TOKEN not found. Either create a .env file or set the environment variable."
        )
    return access_token


def get_top_repos(
    n_repos: int,
    last_n_days: int,
    language: str = None,
    sort: str = "stars",
    order: str = "desc",
) -> Dict[str, Dict]:
    """
    Query for repos created in the last n days

    :param n_repos: Number of repos to return
    :param last_n_days: Number of days to look back
    :param language: Language to filter by
    :param sort: Sort by stars, forks, or updated
    :param order: Order by asc or desc
    :return: Dictionary of repo data
    """
    access_token = get_access_token()
    url = "https://api.github.com/search/repositories"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {access_token}",
    }

    query = f"language:{language}" if language else "is:public"
    date_since = (datetime.now() - timedelta(days=last_n_days)).strftime("%Y-%m-%d")
    query += f" created:>{date_since}"

    repos = []
    page = 1
    while len(repos) < n_repos:
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": 100,
            "page": page,
        }

        with requests.Session() as session:
            session.headers.update(headers)
            try:
                response = session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                repos.extend(data.get("items", []))
            except requests.exceptions.HTTPError as errh:
                print(f"HTTP Error: {errh}")
            except requests.exceptions.ConnectionError as errc:
                print(f"Error Connecting: {errc}")
            except requests.exceptions.Timeout as errt:
                print(f"Timeout Error: {errt}")
            except requests.exceptions.RequestException as err:
                print(f"Unknown Error: {err}")
                break

        # Increment the page number for the next iteration
        page += 1

    # Return only the number of repositories requested
    return repos[:n_repos]


def pull_code_helper(repo_key, branch, delete, max_retries=3):
    """rmtree and retry on intermittent errors"""
    retries = 0
    while retries < max_retries:
        try:
            data = pull_code_from_repo(repo_key, branch=branch, delete=delete)
            return data
        except InvalidGitRepositoryError:
            print(f"Error with {repo_key}, retrying... ({retries + 1}/{max_retries})")
            shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)
            retries += 1

    print(
        f"Failed to pull data from {repo_key} after {max_retries} attempts. Skipping..."
    )
    return None


def pipeline_fetch_and_load(
    n_repos: int,
    last_n_days: int,
    language: str = None,
    sort: str = "stars",
    order: str = "desc",
    delete: bool = False,
) -> Dict[str, Dict]:
    # remove any old repos
    if os.path.exists(REPODATA_FOLDER):
        shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)

    response = get_top_repos(
        n_repos=n_repos,
        last_n_days=last_n_days,
        language=language,
        sort=sort,
        order=order,
    )

    github_data = {}
    for i, repo_metadata in enumerate(response):
        repo_key = repo_metadata["html_url"]

        if repo_metadata["size"]:
            print(f"({i}) Processing {repo_key}...")

            github_data[repo_key] = {}
            github_data[repo_key]["metadata"] = repo_metadata

            response = pull_code_helper(
                repo_key,
                branch=repo_metadata["default_branch"],
                delete=delete,
            )
            if response:
                github_data[repo_key]["docs"] = response
            else:
                del github_data[repo_key]
        else:
            print(f"Skipping {repo_key} as it is empty")

    # clean up repo data
    shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)

    return github_data
