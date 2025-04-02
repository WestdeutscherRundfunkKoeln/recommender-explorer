import json
import pathlib
from typing import Any
import argparse

from envyaml import EnvYAML
from jsonschema import Draft202012Validator, ValidationError
from jsonschema.exceptions import best_match

root_path = pathlib.Path(__file__).parent.parent


def validate_schema(schema_path: str, config: dict[str, Any]) -> None:
    with open(root_path / schema_path) as f:
        schema = json.load(f)

    errors = Draft202012Validator(schema).iter_errors(config)
    err = best_match(errors)
    if not err:
        print(f"Config is valid for schema: {schema_path}")
        return

    msg = ["\n-------------"]
    for sub_err in sorted(err.context, key=lambda e: -len(e.absolute_path)):
        if sub_err.validator in ["anyOf", "oneOf", "allOf"]:
            continue
        msg.append(
            ".".join(
                str([p]) if isinstance(p, int) else p for p in sub_err.absolute_path
            )
            + " is "
            + f"'{sub_err.instance}'"
        )
        msg.append(sub_err.message)
        msg.append("-------------")

    if len(msg) > 1:
        raise ValidationError(message="\n".join(msg)) from err
    raise err


def load_ui_config(config: dict[str, Any], config_path: pathlib.Path) -> dict[str, Any]:
    ui_config = config.get("ui_config")
    if not ui_config:
        print("No ui_config found in config")
        return {}

    if isinstance(ui_config, dict):
        return ui_config

    ui_config_path = config_path.parent / ui_config
    return (
        EnvYAML(ui_config_path, flatten=False).export()
        if isinstance(ui_config, str)
        else {"ui_config": ui_config}
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate config")
    parser.add_argument("--config", type=str, dest="config_path", required=True)
    parser.add_argument(
        "--schema", type=str, dest="schema_path", default="config/schema/schema.json"
    )
    parser.add_argument(
        "--ui_schema",
        type=str,
        dest="ui_schema_path",
        default="config/schema/ui_schema.json",
    )
    args = parser.parse_args()

    config_path = root_path / args.config_path
    config = EnvYAML(config_path, flatten=False, strict=False).export()
    validate_schema(args.schema_path, config)
    print("Config validated")

    ui_config = load_ui_config(config, config_path)
    if ui_config:
        validate_schema(args.ui_schema_path, ui_config)
        print("UI Config validated")
