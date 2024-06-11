import json
import pathlib
from typing import Any

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
        )
        msg.append(sub_err.message)
        msg.append(sub_err.validator)
        msg.append("-------------")

    raise ValidationError(message="\n".join(msg)) from err


def load_ui_config(config: dict[str, Any]) -> dict[str, Any]:
    ui_config = config.get("ui_config")
    if not ui_config:
        print("No ui_config found in config")
        return {}
    return (
        EnvYAML(ui_config, flatten=False).export()
        if isinstance(ui_config, str)
        else {"ui_config": ui_config}
    )


if __file__ == "__main__":
    config = EnvYAML(root_path / "config/config_mediathek.yaml", flatten=False).export()
    validate_schema("config/schema/schema.json", config)
    print("Config validated")

    ui_config = load_ui_config(config)
    validate_schema("config/schema/ui_schema.json", config)
    print("UI Config validated")
