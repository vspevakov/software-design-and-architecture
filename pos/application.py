from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Optional, Protocol

from .domain import Criterion, FinalScoreCalculator, GradebookEntry, Rubric, Student


class GradebookRepository(Protocol):
    def add(self, entry: GradebookEntry) -> None: ...
    def get(self, student_id: str) -> GradebookEntry: ...
    def save(self, entry: GradebookEntry) -> None: ...
    def entries(self) -> Iterable[GradebookEntry]: ...


@dataclass(frozen=True)
class Result:
    student: Student
    course_total: Optional[Fraction]
    current_result: Optional[Fraction]


class ResultExporter(Protocol):
    def export(self, results: Iterable[Result], path: Path) -> None: ...


class AssessmentFacade:
    def __init__(self, rubric: Rubric, repository: GradebookRepository,
                 course: FinalScoreCalculator, current: FinalScoreCalculator,
                 exporter: ResultExporter):
        self._rubric = rubric
        self._repository = repository
        self._course = course
        self._current = current
        self._exporter = exporter

    def add_student(self, student_id: str, name: str) -> None:
        self._repository.add(GradebookEntry(Student(student_id, name), self._rubric))

    def students(self) -> list[Student]:
        return [entry.student for entry in self._repository.entries()]

    def add_criterion(self, criterion_id: str, name: str, maximum: int, weight: Fraction) -> None:
        self._rubric.add_criterion(criterion_id, name, maximum, weight)

    def criteria(self) -> tuple[Criterion, ...]:
        return self._rubric.criteria()

    def set_score(self, student_id: str, criterion_id: str, score: int) -> None:
        entry = self._repository.get(student_id)
        entry.set_score(criterion_id, score)
        self._repository.save(entry)

    def cancel_score(self, student_id: str, criterion_id: str) -> None:
        entry = self._repository.get(student_id)
        entry.cancel_score(criterion_id)
        self._repository.save(entry)

    def scores(self, student_id: str) -> list[tuple[Criterion, Optional[int]]]:
        return self._repository.get(student_id).scores()

    def _result(self, entry: GradebookEntry) -> Result:
        # И меню, и CSV получают итоги по актуальным оценкам через этот метод.
        return Result(entry.student, self._course.calculate(entry), self._current.calculate(entry))

    def result(self, student_id: str) -> Result:
        return self._result(self._repository.get(student_id))

    def export_results(self, path: Path) -> None:
        self._exporter.export((self._result(e) for e in self._repository.entries()), path)
