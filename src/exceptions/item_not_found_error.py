class UnknownItemError(Exception):
    def __init__(self, endpoint, id, errors):
        msg = f"Item with primary id [{id}] not found in endpoint [{endpoint}]"
        super().__init__(msg)

        # Now for your custom code...
        self.errors = errors

