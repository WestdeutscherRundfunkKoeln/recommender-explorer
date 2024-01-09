# Recommender Explorer

Recommender Explorer is a tool for evaluating and testing c2c and u2c recommendations. It contains the ARD Mediathek content pool. Users can select the start content by various means (date range, url, crid) and manipulate the generated recommendations with various filter and ranking widgets. It's also possible to compare the results of different models and algorithms.

The Url of Recommender Explorer is [https://empfehlungsexplorer.ki.wdr.de/](https://empfehlungsexplorer.ki.wdr.de/). Access is protected by a simple username and password combination, which can be obtained from cc.aianalytics@wdr.de

## Infos for developers

Recommender Explorer is a python application based on Panel.

Key architectural components of the application are:

+ Python >3.10
+ [Panel](https://panel.holoviz.org/)
+ [Opensearch]([https://aws.amazon.com/de/what-is/opensearch/])

Recommender Explorer roughly follows the [MVC pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)

In order to a run a development instance of RecoExplorer, you have to expose two environment variables:

```
OPENSEARCH_PASS=******
OPENSEARCH_HOST=******
```

The real values of the variables can be obtained from [cc.aianalytics@wdr.de](mailto:cc.aianalytics@wdr.de).

### Set up AWS connectivity
In your home directory, create a folder and the following files:

> ***Folder-Structure***
> 
> ```
> /home/<username>
> └──.aws
>    ├──config
>    └──credentials
> ```

> ***~/.aws/config***
> 
> ```
> [default]
> region=eu-central-1
> output=json
> ```

#### Generate Acsess-Token
In your AWS Console, navigate to ***Account > Security Credentials > Access Keys***. 
Generate an access key and copy it into the `~/.aws/credentials` file.

> ***~/.aws/credentials***
> ```
> [default]
> aws_access_key_id=<access_key_id>
> aws_secret_access_key=<secret_access_key>
> ```


#### Generate MFA Short-Term Access-Token
*(If your account doesn't require Multi-Factor Authentication, you can skip this step.)*

The credentials generated in the previous step are not sufficient for application use if your account require Multi-Factor Authentication.
To generate a compatible Access-Token we can use the previous credentials in a separate profile.
Open your `~/.aws/credentials` file and replace the default within square brackets with a profile name of your choice.  
 

Update your credentials file as follows.
> ***~/.aws/credentials***
> ```
> -[default]
> +[<profile-name>]
> aws_access_key_id=<access_key_id>
> aws_secret_access_key=<secret_access_key>
> ```

In your AWS Console, navigate to ***Account > Security Credentials > Multi-factor Authentication***.  
Copy the identifier of your MFA device. If there are no MFA devices listed, you will need to set one up.

Open the AWS CLI and paste the following command into it. Use the ***profile-name*** from your credentials file, the ***mfa-identifier***, and a ***token*** generated from this device.
```
aws --profile <profile-name> sts get-session-token --serial-number <mfa-device-identifier> --token-code <mfa-device-token>
```
Your output will look like this:

```
"Credentials": {
        "AccessKeyId": "<session_access_key_id>",
        "SecretAccessKey": "<session_aws_secret_access_key>",
        "SessionToken": "<session_token>",
        "Expiration": "<expiration_date>"
    }
```

Copy the acquired values into your credentials file under the default profile. Your final credentials file should look like this:
> ***~/.aws/credentials***
> ```
> [default]
> aws_access_key_id=<session_access_key_id>
> aws_secret_access_key=<session_aws_secret_access_key>
> aws_session_token=<session_token>
> 
> [<profile-name>]
> aws_access_key_id=<access_key_id>
> aws_secret_access_key=<secret_access_key>
> ```

***Expiration:***
When the generated token expires, you will need to run the command again to generate a new token

#### 

## Set up Recommender Explorer

#### checkout the sources
```git clone git@gitlab.com:ard.de/bi/recommender-explorer.git <local_path>```

#### create a virtual environment and install dependencies

```
python3 -m venv ~/my_envs/reco-xplorer
source ~/my_envs/reco-xplorer/bin/activate
pip3 install -r requirements.txt
```

> ***For windows:***
> ```
> python -m venv my_envs/reco-xplorer
> source my_envs/reco-xplorer/bin/activate
> pip install -r requirements.txt
> ```

## Start Recommender Explorer in development mode
```panel serve RecoExplorer.py -- autoload --show```

## Add and configure a local PA-Service instance
```cp config/config_default.yaml config/config_local.yaml```
+ Edit config/config_local.yaml and add

```
   PA-Service-local:
        handler: 'NnSeekerPaService@model.rest.nn_seeker_paservice'
        endpoint: 'http://localhost:5000/ard/recommendation/content2content'
        start_color: '#669999'
        reco_color: '#d0e1e1'
        default: False
```    
Start application with local config file 

```panel serve RecoExplorer.py --autoreload --show --args config=./config/config_local.yaml```

## Build deployable Docker image
```docker build --no-cache -t reco_explorer:0.1 . ```

## Run Docker image
```docker run --env OPENSEARCH_PASS="OPENSEARCH_PASS" --rm -it -p 8080:80 --name recoxplorer reco_explorer:0.1```


