import yaml
import json
import os


def inject_secret_to_config():
    secret = os.getenv("EMBEDDING_SERVICE_GCS_SERVICE_ACCOUNT_KEY")
    if secret is None:
        raise ValueError("EMBEDDING_SERVICE_GCS_SERVICE_ACCOUNT_KEY environment variable is not set")

    config_path = "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    config["service_account"] = json.loads(secret)

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


if __name__ == "__main__":
    inject_secret_to_config()
