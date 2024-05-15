class ConfigError(Exception):
    def __init__(self, message, errors):
        super().__init__(message)

        # Now for your custom code...
        self.errors = errors
        self.message = message
