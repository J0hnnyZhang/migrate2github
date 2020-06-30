import json
import sys
from base64 import b64encode
from collections import namedtuple

import urllib3

sys.path.append("../migrate_2_github")

from migration.conf import config

Github = namedtuple("Github", ["org", "user", "password"])
BitBucket = namedtuple("BitBucket", ["workspace", "project", "user", "password"])

http = urllib3.PoolManager()


def basic_auth(user, password):
    basic = b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {basic}"


def parse_repo_info(repos):
    return {repo['name']: repo['links']['clone'] for repo in repos}


def fetch_repositories():
    repositories = {}
    page = 13
    while 1:
        print(f"Fetch repos of page {page} ...")
        result = get_repo(page)
        if not result:
            break
        repos = result['values']
        if not repos:
            break
        repositories.update(parse_repo_info(repos))

        with open(f"repository_{page:03}.json", 'w') as f:
            json.dump(repositories, f)

        page += 1
        if page > result['size']:
            break

    return repositories


def get_repo(page):
    url = f"https://api.bitbucket.org/2.0/repositories/{bit_bucket.workspace}?q=project.key%3D%22{bit_bucket.project}%22&page={page}"
    try:
        resp = http.request('GET', url, headers={"Authorization": basic_auth(bit_bucket.user, bit_bucket.password)})
        if resp.status == 200:
            return json.loads(resp.data.decode('utf-8'))
        return None
    except Exception as e:
        print(e)


def create_repository(repository):
    if github.org:
        url = f"https://api.github.com/orgs/${github.org}/repos"
    else:
        url = f"https://api.github.com/user/${github.user}/repos"

    data = {
        "name": repository.slug,
        "description": repository.description,
        "private": repository.is_private,
        "has_issues": repository.has_issues,
        "has_wiki": repository.has_wiki
    }
    # requests.post(url, )


if __name__ == '__main__':
    github_conf = config['github']
    github = Github(github_conf['org'], github_conf['user'], github_conf['password'])

    bitbucket_conf = config['bitbucket']
    bit_bucket = BitBucket(bitbucket_conf["workspace"], bitbucket_conf['project'], bitbucket_conf['user'], bitbucket_conf['password'])

    fetch_repositories()
