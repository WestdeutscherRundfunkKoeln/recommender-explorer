#!/bin/bash
usage() { echo "$0 usage:" && grep " .)\ #" $0; exit 0; }
[ $# -eq 0 ] && usage

SCHEMA_FILE="config/schema/schema.json"
UI_SCHEMA_FILE="config/schema/ui_schema.json"
while getopts "hc:s::u::" arg; do
  case $arg in
    c) # Specify path to the configuration file.
      CONFIG_FILE=${OPTARG}
      ;;
    s) # Specify path to the schema file, default: "config/schema/schema.json".
      SCHEMA_FILE=${OPTARG}
      ;;
    u) # Specify path to the ui schema file, default: "config/schema/ui_schema.json".
      UI_SCHEMA_FILE=${OPTARG}
      ;;
    h) # Display help.
      usage
      ;;
    *) 
    exit 1
      ;;
  esac
done

if [ -z "$CONFIG_FILE" ]; then
  echo "Please specify the path to the configuration file."
  exit 1
fi

python scripts/validate.py --config $CONFIG_FILE --schema $SCHEMA_FILE --ui_schema $UI_SCHEMA_FILE || exit 1

panel serve src/RecoExplorer.py --autoreload --show --args config=$CONFIG_FILE


