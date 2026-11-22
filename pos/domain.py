from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional, Protocol


class DomainError(ValueError):
    """Нарушено правило ведомости."""


class ScoreOutOfRange(DomainError):
    pass


def require_text(value: str, label: str) -> None:
    if not value.strip():
        raise DomainError(f"{label} не может быть пустым.")


@dataclass(frozen=True)
class Student:
    id: str
    # Два объекта Student с одним ID представляют студента даже при изменении имени.
    name: str = field(compare=False)

    def __post_init__(self):
        require_text(self.id, "ID студента")
        require_text(self.name, "Имя студента")


@dataclass(frozen=True)
class Criterion:
    id: str
    name: str
    max_score: int
    weight: Fraction

    def __post_init__(self):
        require_text(self.id, "ID")
        require_text(self.name, "Название")
        if type(self.max_score) is not int or self.max_score <= 0:
            raise DomainError("Максимальный балл должен быть целым и больше нуля.")
        if not isinstance(self.weight, (int, Fraction)) or self.weight <= 0:
            raise DomainError("Вес должен быть положительным рациональным числом.")


@dataclass(frozen=True)
class Evaluation:
    criterion: Criterion
    score: int

    def __post_init__(self):
        if type(self.score) is not int or not 0 <= self.score <= self.criterion.max_score:
            raise ScoreOutOfRange(f"Введите целый балл от 0 до {self.criterion.max_score}.")


class Rubric:
    def __init__(self):
        self._criteria: dict[str, Criterion] = {}

    def add_criterion(self, id: str, name: str, max_score: int, weight: Fraction) -> None:
        if id in self._criteria:
            raise DomainError(f"Критерий {id} уже существует.")
        self._criteria[id] = Criterion(id, name, max_score, weight)

    def criteria(self) -> tuple[Criterion, ...]:
        return tuple(self._criteria.values())

    def create_evaluation(self, criterion_id: str, score: int) -> Evaluation:
        try:
            criterion = self._criteria[criterion_id]
        except KeyError:
            raise DomainError(f"Критерия {criterion_id} нет в рубрикаторе.") from None
        return Evaluation(criterion, score)


class GradebookEntry:
    def __init__(self, student: Student, rubric: Rubric):
        self._student = student
        self._rubric = rubric
        self._evaluations: dict[str, Evaluation] = {}

    @property
    def student(self) -> Student:
        return self._student

    def set_score(self, criterion_id: str, score: int) -> None:
        # Сначала проверяем новую оценку. Если фабрика отклонит балл, прежняя оценка сохранится.
        evaluation = self._rubric.create_evaluation(criterion_id, score)
        self._evaluations[criterion_id] = evaluation

    def get_score(self, criterion_id: str) -> Optional[int]:
        evaluation = self._evaluations.get(criterion_id)
        return evaluation.score if evaluation is not None else None

    def scores(self) -> list[tuple[Criterion, Optional[int]]]:
        # Обходим весь рубрикатор, чтобы в ведомости были видны и критерии с пропусками.
        return [(criterion, self.get_score(criterion.id)) for criterion in self._rubric.criteria()]

    def cancel_score(self, criterion_id: str) -> None:
        if criterion_id not in self._evaluations:
            raise DomainError("По этому критерию у студента нет оценки.")
        del self._evaluations[criterion_id]


class ScoringPolicy(Protocol):
    def include(self, score: Optional[int]) -> bool: ...


class CourseTotal:
    def include(self, score: Optional[int]) -> bool:
        return True


class CurrentResult:
    def include(self, score: Optional[int]) -> bool:
        # Ноль — выставленный балл. Только None означает, что преподаватель ещё не поставил оценку.
        return score is not None


class FinalScoreCalculator:
    def __init__(self, policy: ScoringPolicy):
        self._policy = policy

    def calculate(self, entry: GradebookEntry) -> Optional[Fraction]:
        weighted_sum = Fraction(0)
        total_weight = Fraction(0)
        for criterion, score in entry.scores():
            if self._policy.include(score):
                # Деление на максимум приводит баллы разных шкал к общей доле перед взвешиванием.
                weighted_sum += criterion.weight * Fraction(score or 0, criterion.max_score)
                total_weight += criterion.weight
        if total_weight == 0:
            return None
        return 100 * weighted_sum / total_weight
