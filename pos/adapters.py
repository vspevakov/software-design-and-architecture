import csv
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Optional

from .application import Result
from .domain import GradebookEntry


class RepositoryError(ValueError):
    pass


class MemoryGradebooks:
    def __init__(self):
        self._entries: dict[str, GradebookEntry] = {}

    def add(self, entry: GradebookEntry) -> None:
        if entry.student.id in self._entries:
            raise RepositoryError(f"Студент {entry.student.id} уже существует.")
        self._entries[entry.student.id] = entry

    def get(self, student_id: str) -> GradebookEntry:
        try:
            return self._entries[student_id]
        except KeyError:
            raise RepositoryError(f"Студент {student_id} не найден.") from None

    def save(self, entry: GradebookEntry) -> None:
        self.get(entry.student.id)
        self._entries[entry.student.id] = entry

    def entries(self) -> Iterable[GradebookEntry]:
        return self._entries.values()


def percent_text(value: Optional[Fraction]) -> str:
    if value is None:
        return ""
    # До вывода процент хранится точной дробью. Здесь округляем его до сотых.
    hundredths = round(value * 100)
    return f"{hundredths // 100}.{hundredths % 100:02d}"


class CsvResultExporter:
    def export(self, results: Iterable[Result], path: Path) -> None:
        with path.open("x", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["student_id", "student_name", "course_percent", "current_percent"])
            for row in results:
                writer.writerow([row.student.id, row.student.name, percent_text(row.course_total),
                                 percent_text(row.current_result)])
