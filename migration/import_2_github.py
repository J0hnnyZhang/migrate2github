import json
import os
import sys
import time
from os import path

sys.path.append(path.dirname(path.dirname(__file__)))
from migration.bitbucket import bit_bucket
from migration.github import github


def create_repo(repo):
    try:
        r = os.system(f"gh repo create {github.org}/{repo} -t {TEAM}")
        if r == 0:
            print(f"Create repo {repo} successfully.")
            return True
        print(f"Create repo {repo} successfully.")
        return False
    except Exception as e:
        print(e)


def import_repo(repo, url):
    cmd = f"gh api repos/{github.org}/{repo}/import -X PUT -f vcs=git -f vcs_url=\"{url}\" -f vcs_username='{bit_bucket.user}' -f vcs_password=\"{bit_bucket.password}\""

    try:
        r = os.system(cmd)
        if r == 0:
            print(f"Import repo {repo} successfully.")
            return True
        print(f"Import repo {repo} successfully.")
        return False
    except Exception as e:
        print(e)


def migrate(json_file):
    with open(json_file) as f:
        repos = json.load(f)
    print(f"Total {len(repos)} repos.")
    count = 1
    for repo_name, urls in repos.items():
        print(f"Start to migrate {repo_name} ...")
        origin_url = urls['https']
        create_repo(repo_name)
        import_repo(repo_name, origin_url)
        print(f"{count} Done...\n\n")
        count += 1
        time.sleep(5)


if __name__ == '__main__':
    TEAM = "$team_name"
    migrate("$json_file")
