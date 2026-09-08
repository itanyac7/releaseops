import os


class Config:
    def __init__(self):
        self.SERVICE_NAME = os.getenv("SERVICE_NAME", "releaseops")
        self.APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")