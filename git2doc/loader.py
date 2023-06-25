import concurrent.futures
from datetime import datetime, timedelta
import dotenv
from git import Blob, Repo
from git.exc import InvalidGitRepositoryError, GitCommandError
import os
import math
from pathlib import Path
import polars as pl
import requests
import shutil
import stat
import time
from typing import List, Optional, Dict


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
    ".tiktoken",
    ".lock",
    ".pack",
    ".sub",
    ".zh_CN",
    ".dae",
    ".zh_CN_tgt",
    ".dat",
    ".tsv",
    ".tokens",
    ".off",
    ".sense",
    ".log",
    ".bvh",
    ".onnx",
    ".gltf",
    ".cif",
    ".geojson",
    ".pkl",
    ".bin",
    ".pdb",
    ".sdf",
    ".xmi",
    ".out",
    ".train",
    ".stl",
    ".kicad_pcb",
]
REPODATA_FOLDER = "./repodata/"


def load_file(item, output_path) -> Optional[dict]:
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

            return {
                "page_content": text_content,
                "file_path": rel_file_path,
                "file_name": item.name,
                "file_type": file_type,
            }
    except Exception as e:
        return None


def load_concurrently(repo, output_path) -> List[dict]:
    """
    Loads all files from the repository in parallel.

    :return: A list of documents
    """

    files: List[dict] = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_item = {
            executor.submit(load_file, item, output_path): item
            for item in repo.tree().traverse()
        }
        for future in concurrent.futures.as_completed(future_to_item):
            file = future.result()
            if file is not None:
                files.append(file)
        executor.shutdown(wait=True)

    return files


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


def files_to_str(repo_data):
    """Convert repo data to raw text"""
    raw_repo = ""
    for item in repo_data:
        if "page_content" in item:
            raw_repo += (
                f"{item['metadata']['file_path']}:\n\n{item['page_content']}\n\n"
            )
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
    repo_files = load_concurrently(repo, output_path)
    repo.close()

    if delete:
        shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)

    return repo_files


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


def get_time_intervals(last_n_days, n_intervals):
    """
    Divide the last_n_days into n_intervals based on number of repositories.
    """
    days_per_interval = last_n_days // n_intervals
    end_date = datetime.now()
    start_date = end_date - timedelta(days=last_n_days)

    intervals = []
    for _ in range(n_intervals):
        next_date = min(start_date + timedelta(days=days_per_interval), end_date)
        intervals.append(
            (start_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d"))
        )
        start_date = next_date

    return intervals


def run_repos_query(url, headers, query, repo_batch_size, max_retries=3, retry_delay=5):
    """Given a query, return a repo metadata"""
    repos = []
    page = 1

    while len(repos) < repo_batch_size:
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 100,
            "page": page,
        }
        with requests.Session() as session:
            session.headers.update(headers)

            retries = 0
            while retries < max_retries:
                try:
                    response = session.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                    repos.extend(data.get("items", []))
                    break
                except Exception:
                    pass

                retries += 1
                if retries < max_retries:
                    time.sleep(retry_delay)
                else:
                    if page >= 10:
                        print(
                            f"Failed to get repos after 10 pages. Returning {len(repos)} repos."
                        )
                        return repos[:repo_batch_size]
        page += 1
    return repos[:repo_batch_size]


def get_repos_orchestrator(
    n_repos: int,
    last_n_days: int,
    language: str = None,
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
    base_query = f"language:{language}" if language else "is:public"

    n_intervals = math.ceil(n_repos / 900) if n_repos > 900 else 1
    intervals = get_time_intervals(last_n_days, n_intervals)
    repo_batch_size = n_repos // n_intervals
    print(
        f"Querying {n_repos} repos, this will be done in {n_intervals} batches"
    )

    repos = []
    for start_date, end_date in intervals:
        query = f"{base_query} created:{start_date}..{end_date}"
        print(f"Query: {repo_batch_size} repos on {start_date} -> {end_date}")

        batch = run_repos_query(url, headers, query, repo_batch_size)
        repos.extend(batch)

    print()
    return repos


def pull_code_helper(repo_key, branch, delete, max_retries=3):
    """rmtree and retry on intermittent errors"""
    retries = 0
    while retries < max_retries:
        try:
            data = pull_code_from_repo(repo_key, branch=branch, delete=delete)
            return data
        except InvalidGitRepositoryError:
            shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)
            retries += 1
        except GitCommandError:
            shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)
            retries += 1
    print(f"Failed to pull data from {repo_key} after {max_retries} attempts.")
    return None


def write_to_parquet(filedata, metadata, base_filename, write_batch_counter):
    """Write data to parquet files and clear the data"""
    print(f"Writing batch {write_batch_counter} containing {len(filedata)} files..")

    folder = "output_data"
    if not os.path.exists(folder):
        os.makedirs(folder)

    pl.DataFrame(filedata).write_parquet(
        f"{folder}/filedata_{base_filename}_{write_batch_counter}.parquet"
    )
    pl.DataFrame(metadata).write_parquet(
        f"{folder}/metadata_{base_filename}_{write_batch_counter}.parquet"
    )


def process_repo(i, repo, metadata, filedata, delete=True):
    """Process a repository and add its data to the metadata and filedata lists."""

    if repo["size"]:
        repo_key = repo["html_url"]
        print(f"({i}) Processing {repo_key}...")

        response = pull_code_helper(
            repo_key,
            branch=repo["default_branch"],
            delete=delete,
        )
        if response:
            metadata_preprocess = flatten_dict(repo)
            metadata.append(metadata_preprocess)

            for file_obj in response:
                file_obj["repo_name"] = repo_key
                filedata.append(file_obj)

    return metadata, filedata


def pipeline_fetch_and_load(
    n_repos: int,
    last_n_days: int,
    language: str = None,
    write_batch_size: int = 100,
) -> None:
    try:
        # cleanup repo data folder
        if os.path.exists(REPODATA_FOLDER):
            shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)

        repos = get_repos_orchestrator(
            n_repos=n_repos,
            last_n_days=last_n_days,
            language=language,
        )

        base_filename = datetime.now().strftime("%Y%m%d%H%M%S")
        write_batch_counter = 1
        metadata = []
        filedata = []

        for i, repo in enumerate(repos):
            metadata, filedata = process_repo(
                i, repo, metadata, filedata
            )

            # If the batch size is reached, write the data to parquet files and clear the lists
            if not (i + 1) % write_batch_size:
                write_to_parquet(filedata, metadata, base_filename, write_batch_counter)
                metadata.clear()
                filedata.clear()
                write_batch_counter += 1

        # Write the remaining data to parquet files
        if metadata and filedata:
            write_to_parquet(filedata, metadata, base_filename, write_batch_counter)

    finally:
        # Always clean up the repo data folder
        if os.path.exists(REPODATA_FOLDER):
            shutil.rmtree(REPODATA_FOLDER, onerror=readonly_to_writable)
