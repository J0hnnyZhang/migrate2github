import os

import yaml


def read_config():
    base_dir = os.path.dirname(__file__)
    config_file = os.environ.get("CONF")
    default_config = os.path.join(base_dir, 'conf-my.yaml')
    config_file = config_file if config_file else default_config
    with open(config_file, 'r') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(e)


config = None
if not config:
    config = read_config()

if __name__ == '__main__':
    print(config)
