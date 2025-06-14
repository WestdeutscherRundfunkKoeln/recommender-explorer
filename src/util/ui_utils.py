def retrieve_default_model_accordion(ui_config):
    # loop through the ui_config file and look for the block Modelle wählen.
    # in Modelle wählen identify the key that points to the active accordion and return it.
    # if the block is called "Modelle wählen" then we should do the search procedure.

    # Access the blocks in the config
    blocks = ui_config.get("blocks", [])

    # Iterate over each block
    for block in blocks:
        # Skip if the label is not "Modelle wählen"
        if block.get("label") != "Modelle wählen":
            continue

        # Iterate over the components within the block
        for component in block.get("components", []):
            # Skip if the component type is not "accordion_with_cards"
            if component.get("type") != "accordion_with_cards":
                continue

            # Get the "active" key value and return it as a string
            active_value = component.get("active")
            return str(active_value) if active_value is not None else None

    # If not found, return a default value
    return str(1)
