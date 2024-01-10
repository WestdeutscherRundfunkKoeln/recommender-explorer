# Recommender Explorer

Recommender Explorer is a tool for evaluating and testing c2c and u2c recommendations. Users can select the start content by various means (date range, url, crid) and manipulate the generated recommendations with various filter and ranking widgets. It's also possible to compare the results of different models and algorithms.

The Url of Recommender Explorer is [https://empfehlungsexplorer.ki.wdr.de/](https://empfehlungsexplorer.ki.wdr.de/). Access is protected by a simple username and password combination, which can be obtained from cc.aianalytics@wdr.de

## Infos for developers

Recommender Explorer is a python application based on Panel.

Key architectural components of the application are:

+ Python
+ [Panel](https://panel.holoviz.org/)
+ [Opensearch]([https://aws.amazon.com/de/what-is/opensearch/])

It roughly follows the [MVC pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)

### Set up Opensearch connectivity

Recommender Explorer uses Opensearch for metadata and vector storage. In order to a run a development instance, you have to expose two variables in your environment:

```
OPENSEARCH_PASS=******
OPENSEARCH_HOST=******
```
of your Opensearch instance. 

### Set up AWS connectivity

Recommender Explorer requires AWS connectivity for models hosted in Sagemaker. Follow the instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) in order to set up AWS connectivity for your development environment.

### Set up Recommender Explorer

#### Checkout the sources
```git clone git@github.com:WestdeutscherRundfunkKoeln/recommender-explorer.git <local_path>```

Copy the file <local_path>/config/config_template.yaml to </path/to/your_config_file.yaml> and configure your model endpoints and mappings accordingly. 

#### Create a virtual environment and install dependencies

```
python3 -m venv ~/my_envs/reco-xplorer
source ~/my_envs/reco-xplorer/bin/activate
pip3 install -r requirements.txt
```

### Start Recommender Explorer in development mode
```panel serve RecoExplorer.py --autoreload --show --args config=</path/to/your_config_file.yaml>```

### Run tests
```pytest --config=</path/to/your_config_file.yaml>```

### Build deployable Docker image
```docker build --no-cache -t reco_explorer:0.1 . ```

### Run Docker image
```docker run --env OPENSEARCH_PASS="<YOUR_OPENSEARCH_PW>" --env AWS_ACCESS_KEY_ID="<YOUR_AWS_KEY_ID>" --env AWS_SECRET_ACCESS_KEY="<YOUR_AWS_SECRET>" --env AWS_DEFAULT_REGION="eu-central-1"   --rm -it -p 8080:80 --name recoxplorer reco_explorer:0.1```

