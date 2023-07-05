import toml


class Config:
    def __init__(self, config_file):
        config_data = toml.load(config_file)
        self.DB_HOST = config_data["DB_HOST"]
        self.DB_PORT = config_data["DB_PORT"]
        self.USER = config_data["USER"]
        self.PASSWORD = config_data["PASSWORD"]
        self.OPTIONS = config_data["OPTIONS"]


config = Config("config.toml")
