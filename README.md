# migrate2github
Migrate repositories to github from other VCS like bitbucket etc.

## Supported
- bitbucket -> github

## How to use
### Migrate from bitbucket to github
The `bitbucket_2_github.py` script is to migrate *all the repositories* of the `project` 
on the bitbucket `workspace` to github, the new repositories will be owned by the specified `org`
if `org` is specified, otherwise, the `org` is empty or null, the new repositories will be owned 
by `user`
#### Two steps
1. Fill the conf.yaml in conf dir
2. Run bitbucket_2_github.py
```shell script
python bitbucket_2_github.py
```
