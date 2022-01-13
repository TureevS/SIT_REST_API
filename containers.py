import os
from dependency_injector import containers
from service import Service


class ApplicationContainer(containers.DeclarativeContainer):
    service = Service(os.environ["FLASK_ENV"])
