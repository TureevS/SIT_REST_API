class Service:
    def __init__(self, app_env: str):
        self.APP_ENV = app_env

    def get(self):
        return self.APP_ENV
