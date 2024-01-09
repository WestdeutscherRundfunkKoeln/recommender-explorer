import sys

from envyaml import EnvYAML
from view.RecoExplorerApp import RecoExplorerApp

def getExplorerInstance():
    return RecoExplorerApp(config).render()

#
# start like so: panel serve RecoExplorer.py --autoreload --show
# or so: panel serve RecoExplorer.py --autoreload --show --args config=./config/config_local.yaml
#
if not len(sys.argv[1:]):
    configuration_file_name = './config/config_default.yaml'
else:
    configuration_file_name = sys.argv[1:][0].removeprefix('config=')

config = EnvYAML(configuration_file_name)
getExplorerInstance().server_doc()
