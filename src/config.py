import os


class Config:
    class App:
        NAME = "data-gatherer"
        VERSION = "0.1.0"
        DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    class Api:
        TITLE = "Data Gatherer API"
        DESCRIPTION = "Manages the data gathering processes for all solvers"
        VERSION = "v1"
        ROOT_PATH = "/"
