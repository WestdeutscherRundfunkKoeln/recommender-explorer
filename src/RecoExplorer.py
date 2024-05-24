import panel as pn
import sys
import logging
from view.RecoExplorerApp import RecoExplorerApp
from util.file_utils import get_config_from_search, get_config_from_arg
from exceptions.config_error import ConfigError

logger = logging.getLogger(__name__)
logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

def getExplorerInstance():
    return RecoExplorerApp(config_full_path).render()

#
# start like so: panel serve RecoExplorer.py --args config=<path_to_my_config.yaml>
#
if not len(sys.argv[1:]):
    exit('Unable to start Reco Explorer - no config was passed.')

try:
    config_full_path = get_config_from_arg(sys.argv[1:][0])

    # replace config from url param, if given
    if pn.state.location.search:
        new_config_full_path = get_config_from_search(pn.state.location.search, config_full_path)
        if new_config_full_path:
            config_full_path = new_config_full_path

    getExplorerInstance().server_doc()

except ConfigError as e:
    logger.critical(e.message)
    RecoExplorerApp.render_404().server_doc()

except Exception as e:
    exit(e)