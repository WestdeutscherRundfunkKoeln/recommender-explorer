import sys

from envyaml import EnvYAML
from view.RecoExplorerApp import RecoExplorerApp
import re
import panel as pn

def getExplorerInstance():
    return RecoExplorerApp(config).render()

#
# start like so: panel serve RecoExplorer.py --autoreload --show
# or so: panel serve RecoExplorer.py --autoreload --show --args config=./config/config_local.yaml
#

# Set default suffix for config
config_default = 'mediathek'

# Find config suffix in url
url = pn.state.location.search
match = re.search(r'(?<=\bmandant=)[^&]+', url)
if match:
    config_suffix = match.group(0)
else:
    config_suffix = config_default
config_file = 'config_' + config_suffix + '.yaml'

if not len(sys.argv[1:]):
    configuration_file_name = '../recommender-explorer-config/' + config_file
else:
    configuration_file_name = sys.argv[1:][0].removeprefix('config=')

config = EnvYAML(configuration_file_name)
getExplorerInstance().server_doc()
