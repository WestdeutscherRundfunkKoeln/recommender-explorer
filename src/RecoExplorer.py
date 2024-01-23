import panel as pn
import sys
import logging
from view.RecoExplorerApp import RecoExplorerApp
from util.file_utils import get_config_from_search, get_config_from_arg

logger = logging.getLogger(__name__)

def getExplorerInstance():
    return RecoExplorerApp(config_full_path).render()

#
# start like so: panel serve RecoExplorer.py --args config=<path_to_my_config.yaml>
#
if not sys.argv[1:][0]:
    exit('Unable to start Reco Explorer - no config was passed.')

try:
    config_full_path = get_config_from_arg(sys.argv[1:][0])

    # replace config from url param, if given
    if pn.state.location.search:
        config_full_path = get_config_from_search(pn.state.location.search, config_full_path)

    getExplorerInstance().server_doc()
except Exception as e:
    exit(e)