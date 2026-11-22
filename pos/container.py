from dependency_injector import containers, providers

from .adapters import CsvResultExporter, MemoryGradebooks
from .application import AssessmentFacade
from .domain import CourseTotal, CurrentResult, FinalScoreCalculator, Rubric


class Container(containers.DeclarativeContainer):
    """Один экземпляр контейнера обслуживает один сеанс ведомости."""
    rubric = providers.Singleton(Rubric)
    repository = providers.Singleton(MemoryGradebooks)
    exporter = providers.Factory(CsvResultExporter)

    course = providers.Factory(FinalScoreCalculator, policy=providers.Factory(CourseTotal))
    current = providers.Factory(FinalScoreCalculator, policy=providers.Factory(CurrentResult))

    assessments = providers.Factory(
        AssessmentFacade,
        rubric=rubric,
        repository=repository,
        course=course,
        current=current,
        exporter=exporter,
    )
