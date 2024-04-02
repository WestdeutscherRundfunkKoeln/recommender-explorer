# Recommender Explorer

Recommender Explorer is a GUI based tool for evaluating and testing content-2-content and user-2-content recommendations. Users can select the start-content by various means (date-range, url, user-cluster, id) and manipulate the generated recommendations with filter and ranking widgets. It's also possible to compare the results of different models and algorithms side-by-side. In addition, Recommender Explorer contains a number of microservices, which can be used to ingest and embed items into an OpenSearch index.

The primary purpose of Recommender Explorer is to provide  a means for interacting with your own, custom recommendation algorithms outside their actual production environment. 

## Infos for developers

Recommender Explorer is a python application based on Panel.

Key architectural components of the application are:

+ Python
+ [Panel](https://panel.holoviz.org/)
+ [OpenSearch]([https://aws.amazon.com/de/what-is/opensearch/])

It roughly follows the [MVC pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)

### Set up Opensearch connectivity

Recommender Explorer uses OpenSearch for metadata and vector storage. In order to a run a development instance of Recommender Explorer, you have to expose two variables to your environment:

```
OPENSEARCH_PASS=******
OPENSEARCH_HOST=******
```
in order to gain access to your OpenSearch instance. 

### Set up AWS connectivity

Recommender Explorer requires AWS connectivity for models hosted in Sagemaker. Follow the instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) in order to set up AWS connectivity for your development environment.

### Set up Recommender Explorer

#### Checkout the sources
```git clone git@github.com:WestdeutscherRundfunkKoeln/recommender-explorer.git <local_path>```

#### Create a virtual environment and install dependencies

```
python3 -m venv ~/my_envs/reco-xplorer
source ~/my_envs/reco-xplorer/bin/activate
pip3 install -r requirements.txt
```

#### Adapt the configuration file
Copy the file <local_path>/config/config_template.yaml to </path/to/your_config_file.yaml> and configure your model endpoints and mappings accordingly. 

### Start Recommender Explorer in development mode
```panel serve RecoExplorer.py --autoreload --show --args config=</path/to/your_config_file.yaml>```

### Run tests
```pytest --config=</path/to/your_config_file.yaml>```

### Build deployable Docker image
```docker build --no-cache -t reco_explorer:0.1 . ```

### Run Docker image
```docker run --env OPENSEARCH_PASS="<YOUR_OPENSEARCH_PW>" --env AWS_ACCESS_KEY_ID="<YOUR_AWS_KEY_ID>" --env AWS_SECRET_ACCESS_KEY="<YOUR_AWS_SECRET>" --env AWS_DEFAULT_REGION="eu-central-1"   --rm -it -p 8080:80 --name recoxplorer reco_explorer:0.1```

## How to contribute

Recommender Explorer as a whole is distributed under the MIT license. You are welcome to contribute code in order to fix bugs or to implement new features. 

There are three important things to know:

1. You must be aware and agree to a Contributors License Agreement (CLA) before you can contribute. However, if your contribution constitutes as a small code contribution, you do not need a CLA. Our CLAs are largely derived from the ones used by Apache Software Foundation (https://www.apache.org/licenses/contributor-agreements.html)
2. There are several requirements regarding code style, quality, and product standards which need to be met (we also have to follow them). 
3. Not all proposed contributions can be accepted. Some features may e.g. just fit a third-party add-on better. The code must fit the overall direction of Recommender Explorer and really improve it. The more effort you invest, the better you should clarify in advance whether the contribution fits: the best way would be to just open an issue to discuss the feature you plan to implement (make it clear you intend to contribute).

### Process of a contribution

- Make sure the change would be welcome (e.g. a bugfix or a useful feature); best do so by proposing it in a GitHub issue on our repository. Also check for similar issues that might already be present. 
- Create a branch forking the Recommender Explorer repository and do your change
- Commit and push your changes on that branch
- In the commit message, describe the problem you fix with this change.
- Describe the effect that this change has from a user's point of view.
- Describe the technical details of what you changed. It is important to describe the change in a most understandable way so the reviewer is able to verify that the code is behaving as you intend it to.
- If your change fixes an issue reported at GitHub, add the following line to the commit message:
Fixes #(issueNumber)
- Create a Pull Request
- Wait for our code review and approval, possibly enhancing your change on request
- Once the change has been approved we will inform you in a comment
- We will close the pull request, feel free to delete the now obsolete branch
