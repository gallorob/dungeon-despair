from argparse import Namespace

import yaml


def dict_to_namespace(d):
    if isinstance(d, dict):
        for key, value in d.items():
            d[key] = dict_to_namespace(value)
        return Namespace(**d)
    elif isinstance(d, list):
        return [dict_to_namespace(item) for item in d]
    else:
        return d


with open("./configs.yml", "r") as file:
    configs = dict_to_namespace(yaml.safe_load(file))
