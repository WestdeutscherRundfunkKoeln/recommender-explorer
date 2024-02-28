# Ingest Service
TODO: Descripe purpose of service

# Parameters and configuration options
TODO:List startup parameters

# Local development 
Start with application with
~~~
FULL_PATH='<your path to config file>' uvicorn microservices.ingestservice.src.main:app --reload
~~~
# Docker container
from ingestservice directory build as
~~~
docker build -t recoxplorer/ingestservice:latest -f docker/Dockerfile .
~~~
run container as
~~~
docker run -p 8080:80 --rm recoxplorer/ingestservice
~~~