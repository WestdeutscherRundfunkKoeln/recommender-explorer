# Ingest Service
TODO: Descripe purpose of service

# Parameters and configuration options
TODO:List startup parameters

# Local development 
Start with application with
~~~
FULL_PATH='<your path to config file>' uvicorn src.main:app --reload
~~~
# Docker container
from ingestservice directory build as
~~~
docker build -t recoxplorer/ingestservice:latest -f docker/Dockerfile .
~~~
run container as
~~~
docker run -e CONFIG_FILE='config.yaml' -e OPENSEARCH_USER=$OPENSEARCH_USER -e OPENSEARCH_HOST=$OPENSEARCH_HOST -e OPENSEARCH_PORT=$OPENSEARCH_PORT -e OPENSEARCH_INDEX=$OPENSEARCH_INDEX -e OPENSEARCH_PASS=$OPENSEARCH_PASS -p 8080:80 --rm recoxplorer/ingestservice
~~~