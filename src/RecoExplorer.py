import logging
import sys

import panel as pn

from exceptions.config_error import ConfigError
from util.file_utils import (
    get_config_from_search,
    get_configs_from_arg,
    load_config,
)
from view.RecoExplorerApp import RecoExplorerApp

logger = logging.getLogger(__name__)
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def getExplorerInstance(
    config_full_paths: dict[str, str], config: dict[str, str], client: str
):
    return RecoExplorerApp(config_full_paths, config, client).render()


#
# Start like so: panel serve src/RecoExplorer.py --args config=<path>
# <path> can be one or more of:
#  - s3://bucket/key.yaml
#  - s3://bucket/ (loads all config_*.yaml in bucket)
#  - local YAML file path
#  - local directory containing config_*.yaml
if not len(sys.argv[1:]):
    import os
    logger.info("No config passed, trying to read from CONFIG_URI")
    env_uri = os.getenv("CONFIG_URI")
    logger.info(f"CONFIG_URI={env_uri}")
    if env_uri:
        sys.argv.append(f"config={env_uri}")
    else:
        exit("Unable to start Reco Explorer - no config was passed. Provide --args config=<s3://...|/local/path> or set CONFIG_URI.")

try:
    client, config_full_path, config_full_paths = get_configs_from_arg(sys.argv[1])

    # replace config from url param, if given
    if pn.state.location.search:
        search = get_config_from_search(pn.state.location.search, config_full_paths)
        if search:
            client, config_full_path = search

    config = load_config(config_full_path)
    config["reco_explorer_url_base"] = pn.state.location.href.replace(
        pn.state.location.search, ""
    )

    getExplorerInstance(config_full_paths, config, client).server_doc()

except ConfigError as e:
    logger.critical(e.message)
    RecoExplorerApp.render_404().server_doc()

except Exception as e:
    exit(e)
