import logging
import re
import glob
import os
import constants

logger = logging.getLogger(__name__)

def get_all_config_files(path) -> list:
    pattern = os.path.dirname(path) + '/' + 'config_[a-z]*.yaml'
    all_configs = glob.glob(pattern)
    return all_configs

def get_config_from_arg(arg) -> str:
    full_path = arg.removeprefix('config=')
    if os.path.isfile(full_path):
        return full_path
    else:
        raise Exception('Config file not found at path [' + full_path + ']')

def get_config_from_search(search, config_full_path) -> str:
    client_ident = _get_client_ident_from_search(search)
    path, name = _segment_arg_config(config_full_path)
    full_path = path + '/' + _replace_config(name, client_ident)
    if os.path.isfile(full_path):
        return full_path
    else:
        raise Exception('Config file from param not found at path [' + full_path + ']')

def _get_client_ident_from_search(search) -> str:
    app_ident = ''
    for pair in search.removeprefix('?').split('&'):
        param, val = list(pair.split('='))
        if param == constants.CLIENT_IDENTIFIER:
            app_ident = val
    if app_ident:
        return app_ident
    else:
        raise Exception('Client identifier not found')

def _segment_arg_config(config_name) -> tuple[str, str]:
    configuration_string = config_name.removeprefix('config=')
    config_path = os.path.dirname(os.path.normpath(configuration_string))
    config_name = os.path.basename(os.path.normpath(configuration_string))
    return config_path, config_name

def _replace_config(config_name, app_ident) -> str:
    replaced_config_name = re.sub("(^config_)(.*)(\.yaml$)", (r"\1" + app_ident + r"\3"), config_name)
    return replaced_config_name