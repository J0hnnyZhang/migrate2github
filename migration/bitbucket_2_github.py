import json
import os
import sys
import time
from base64 import b64encode
from collections import namedtuple
from os import path, mkdir
from os.path import expanduser

import urllib3

sys.path.append(path.dirname(path.dirname(__file__)))

from migration.conf import config

Github = namedtuple("Github", ["org", "user", "password", "token"])
BitBucket = namedtuple("BitBucket", ["workspace", "project", "user", "password"])

http = urllib3.PoolManager()


def basic_auth(user, password):
    basic = b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {basic}"


def parse_repo_info(repos):
    return {repo['name']: repo['links']['clone'] for repo in repos}


def fetch_repositories():
    repositories = {}
    page = 1
    while 1:
        print(f"Fetch repos of page {page} ...")
        result = get_repo(page)
        if not result:
            break
        repos = result['values']
        if not repos:
            break
        repositories.update(parse_repo_info(repos))
        page += 1
        if page > result['size']:
            break
    repos_json_file = f"origin_repository_{page:03}.json"
    with open(repos_json_file, 'w') as f:
        json.dump(repositories, f)
    return repositories, repos_json_file


def get_repo(page):
    url = f"https://api.bitbucket.org/2.0/repositories/{bit_bucket.workspace}?q=project.key%3D%22{bit_bucket.project}%22&page={page}"
    try:
        resp = http.request('GET', url, headers={"Authorization": basic_auth(bit_bucket.user, bit_bucket.password)})
        if resp.status == 200:
            return json.loads(resp.data.decode('utf-8'))
        return None
    except Exception as e:
        print(e)


def create_repositories_from_json_file(json_file):
    with open(json_file) as f:
        repos = json.load(f)

    all_repos = {}
    for key, urls in repos.items():
        time.sleep(2)
        github_urls = check_exists(key)
        if not github_urls:
            github_urls = create_repository(key)
        if github_urls:
            print(f"Create repository success, {key}")
            all_repos[key] = {
                "origin_url": urls,
                "github_url": github_urls
            }
        else:
            print(f"Create repository failed, {key}")
    merged_json_file = "all_repositories.json"
    with open(merged_json_file, 'w') as f:
        json.dump(all_repos, f)
    return all_repos, merged_json_file


def check_exists(repo_name):
    if github.org:
        url = f"https://api.github.com/repos/{github.org}/{repo_name}"
    else:
        url = f"https://api.github.com/repos/{github.user}/{repo_name}"
    try:
        resp = http.request("GET", url, headers={'Content-Type': 'application/json', "Authorization": f"Bearer {github.token}", "User-Agent": "I'm UA", })
        if resp.status == 200:
            result = json.loads(resp.data.decode('utf-8'))
            return {
                "git_url": result['git_url'],
                "ssh_url": result['ssh_url'],
            }
    except Exception as e:
        print(e)
        return None


def create_repository(repo_name):
    if github.org:
        url = f"https://api.github.com/orgs/{github.org}/repos"
    else:
        url = f"https://api.github.com/user/{github.user}/repos"

    data = {
        "name": repo_name,
        "description": "",
        "private": True,
        "has_issues": False,
        "has_wiki": False
    }
    encoded_data = json.dumps(data).encode('utf-8')
    try:
        resp = http.request("POST", url, headers={'Content-Type': 'application/json', "Authorization": f"Bearer {github.token}", "User-Agent": "I'm UA", }, body=encoded_data)
        if resp.status == 200:
            result = json.loads(resp.data.decode('utf-8'))
            return {
                "git_url": result['git_url'],
                "ssh_url": result['ssh_url'],
            }
        else:
            print(json.loads(resp.data.decode('utf-8')))
            return None
    except Exception as e:
        print(e)


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
    github_conf = config['github']
    github = Github(github_conf['org'], github_conf['user'], github_conf['password'], github_conf['token'])

    bitbucket_conf = config['bitbucket']
    bit_bucket = BitBucket(bitbucket_conf["workspace"], bitbucket_conf['project'], bitbucket_conf['user'], bitbucket_conf['password'])

    _, json_file = fetch_repositories()
    _, all_json_file = create_repositories_from_json_file(json_file)
    migrate(all_json_file)
