import json
import os
import sys
from os import path, mkdir
from os.path import expanduser

sys.path.append(path.dirname(path.dirname(__file__)))

from migration.bitbucket import bit_bucket


def _repo_path(repo_name):
    home = expanduser("~")
    repo_path_ = path.join(home, f"repo-migration/{bit_bucket.workspace}/{bit_bucket.project}")
    if not path.exists(repo_path_):
        mkdir(repo_path_)
    repo = path.join(repo_path_, repo_name)
    if not path.exists(repo):
        mkdir(repo)
    return repo


def pull(repo_path, url):
    try:
        r = os.system(f"cd {repo_path} && git clone --bare {url} && cd ../")
        if r == 0:
            print(f"Pull {url} done")
            return True
    except Exception as e:
        print(e)
    return False


def push(repo_path, url):
    try:
        url = url.replace("git://", "https://")
        fname = path.split(repo_path)[-1]
        repo_path = f"{repo_path}/{fname}.git"
        r = os.system(f"cd {repo_path} && git push --mirror {url} && cd ../")
        if r == 0:
            print(f"Push {url} done")
            return True
    except Exception as e:
        print(e)
    return False


def migrate(repos_json):
    with open(repos_json) as f:
        repos = json.load(f)

    failed = []
    for name, urls in repos.items():
        repo_path = _repo_path(name)
        origin_url = urls['origin_url'][0]['href']
        github_url = urls['github_url']['git_url']
        print(f"Start to pull {name}: {origin_url} ")
        if pull(repo_path, origin_url):
            print(f"Start to push {name}: {github_url}")
            push(repo_path, github_url)
        else:
            failed.append({repo_path: [origin_url, github_url]})
        print("\n")

    if failed:
        print(f"Failed, {failed}")


if __name__ == '__main__':
    repos_json_file = ""
    migrate(repos_json_file)
