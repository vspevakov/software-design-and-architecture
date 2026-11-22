from .cli import run
from .container import Container


if __name__ == "__main__":
    container = Container()
    run(container.assessments())
