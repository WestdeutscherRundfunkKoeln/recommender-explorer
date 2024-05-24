import logging
import re
import glob
import os
import constants
import re
from exceptions.config_error import ConfigError

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
    client_ident = get_client_ident_from_search(search)
    if client_ident:
        path, name = _segment_arg_config(config_full_path)
        full_path = path + '/' + _replace_config(name, client_ident)
        if os.path.isfile(full_path):
            return full_path
        else:
            raise ConfigError('Config file from search param [' + search + '] not found at path [' + full_path + ']', {})

def get_client_from_path(full_path):
    match = re.search(r'/config_(\w+)\.yaml$', full_path)

    # Check if a match is found and return the config name
    if match:
        return match.group(1)
    else:
        raise Exception('Client could not be matched from path [' + full_path + ']')

def get_client_ident_from_search(search) -> str:
    app_ident = ''
    for pair in search.removeprefix('?').split('&'):
        param, val = list(pair.split('='))
        if param == constants.CLIENT_IDENTIFIER:
            app_ident = val
    if app_ident:
        return app_ident
    # else:
        # raise Exception('Client identifier not found')

def get_client_options(config_full_path):
    all_configs = get_all_config_files(config_full_path)
    options = {}
    for config_path in all_configs:
        client = get_client_from_path(config_path)
        key = client.capitalize() # Capitalize the first letter of the client for the key
        options[key] = client
    return options

def _segment_arg_config(config_name) -> tuple[str, str]:
    configuration_string = config_name.removeprefix('config=')
    config_path = os.path.dirname(os.path.normpath(configuration_string))
    config_name = os.path.basename(os.path.normpath(configuration_string))
    return config_path, config_name

def _replace_config(config_name, app_ident) -> str:
    replaced_config_name = re.sub("(^config_)(.*)(\.yaml$)", (r"\1" + app_ident + r"\3"), config_name)
    return replaced_config_name