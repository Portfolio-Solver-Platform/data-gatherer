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

    class RabbitMQ:
        HOST = os.getenv("RABBITMQ_HOST")
        PORT = int(os.getenv("RABBITMQ_PORT"))
        USER = os.getenv("RABBITMQ_USER")
        PASSWORD = os.getenv("RABBITMQ_PASSWORD")

    PROJECT_ID = os.getenv("PROJECT_ID")
    CONTROL_QUEUE = os.getenv("CONTROL_QUEUE")
    DIRECTOR_QUEUE = os.getenv("DIRECTOR_QUEUE")
    PROJECT_SOLVER_RESULT_QUEUE = os.getenv("PROJECT_SOLVER_RESULT_QUEUE")
    SOLVER_DIRECTOR_RESULT_QUEUE = os.getenv("SOLVER_DIRECTOR_RESULT_QUEUE")




