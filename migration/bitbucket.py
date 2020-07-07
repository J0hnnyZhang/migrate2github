import json
import sys
from base64 import b64encode
from collections import namedtuple
from os import path

sys.path.append(path.dirname(path.dirname(__file__)))
from migration.conf import config
from migration.http_helper import http

BitBucket = namedtuple("BitBucket", ["workspace", "project", "user", "password"])

bitbucket_conf = config['bitbucket']
bit_bucket = BitBucket(bitbucket_conf["workspace"], bitbucket_conf['project'], bitbucket_conf['user'], bitbucket_conf['password'])


def _basic_auth(user, password):
    basic = b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {basic}"


def _parse_repo_info(repos):
    return {repo['name']: {"https": repo['links']['clone'][0]['href'],
                           "ssh": repo['links']['clone'][1]['href']} for repo in repos}


def get_repo(page):
    url = f"https://api.bitbucket.org/2.0/repositories/{bit_bucket.workspace}?q=project.key%3D%22{bit_bucket.project}%22&page={page}"
    try:
        resp = http.request('GET', url, headers={"Authorization": _basic_auth(bit_bucket.user, bit_bucket.password)})
        if resp.status == 200:
            return json.loads(resp.data.decode('utf-8'))
        return None
    except Exception as e:
        print(e)


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
        repositories.update(_parse_repo_info(repos))
        if page + 1 > result['size']:
            break
        page += 1
    repos_json_file = f"bitbucket_{bit_bucket.workspace}_{bit_bucket.project}_{page:03}.json"
    with open(repos_json_file, 'w') as f:
        json.dump(repositories, f)
    return repositories, repos_json_file


if __name__ == '__main__':
    fetch_repositories()
