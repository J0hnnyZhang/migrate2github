import json
import sys
import time
from collections import namedtuple
from os import path

sys.path.append(path.dirname(path.dirname(__file__)))
from migration.http_helper import http
from migration.conf import config

Github = namedtuple("Github", ["org", "user", "password", "token"])

github_conf = config['github']
github = Github(github_conf['org'], github_conf['user'], github_conf['password'], github_conf['token'])


def create_repositories(json_file):
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
    merged_json_file = "merged_repositories.json"
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


def delete(repo):
    if github.org:
        url = f"https://api.github.com/repos/{github.org}/{repo}"
    else:
        url = f"https://api.github.com/repos{github.user}/{repo}"

    try:
        resp = http.request("DELETE", url, headers={'Content-Type': 'application/json', "Authorization": f"Bearer {github.token}", "User-Agent": "I'm UA", })
        if resp.status == 204:
            print(f"Delete github {repo} successfully.")
            return True
        else:
            print(f"Delete github {repo} failed.")
            print(json.loads(resp.data.decode('utf-8')))
            return False
    except Exception as e:
        print(e)


def delete_from_json(json_file):
    with open(json_file) as f:
        repos = json.load(f)
    for key, urls in repos.items():
        delete(key)
