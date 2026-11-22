import csv
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


class ConsoleTests(unittest.TestCase):
    def test_grading_correction_cancellation_and_csv_export(self):
        with TemporaryDirectory() as directory:
            before = Path(directory) / "before.csv"
            after = Path(directory) / "after.csv"
            commands = [
                ["1", "s1", "Анна, В."],
                ["1", "s2", "Борис"],
                ["2"],
                ["3", "project", "Проект", "10", "1,5"],
                ["3", "exam", "Защита", "5", "0,5"],
                ["4"],
                ["5", "s1", "project", "8"],
                ["5", "s1", "project", "12"],
                ["5", "s1", "unknown", "3"],
                ["6", "s1"],
                ["5", "s1", "exam", "3"],
                ["8", "s1"],
                ["9", str(before)],
                ["5", "s1", "exam", "5"],
                ["8", "s1"],
                ["7", "s1", "exam"],
                ["8", "s1"],
                ["9", str(after)],
                ["0"],
            ]
            inputs = "\n".join(value for command in commands for value in command) + "\n"
            process = subprocess.run(
                [sys.executable, "-B", "-m", "pos"],
                cwd=Path(__file__).resolve().parents[1],
                input=inputs, text=True, capture_output=True, check=True, timeout=10,
            )
            for message in (
                "s2 — Борис", "максимум 10, вес 3/2", "Введите целый балл от 0 до 10",
                "Критерия unknown нет", "Проект (project) — 8/10", "Защита (exam) — пока нет оценки",
                "итог курса 75.00%", "итог курса 85.00%", "итог курса 60.00%",
                "Текущий результат: 80.00%",
            ):
                with self.subTest(message=message):
                    self.assertIn(message, process.stdout)

            for path, course, current in [(before, "75.00", "75.00"), (after, "60.00", "80.00")]:
                with self.subTest(file=path.name), path.open(encoding="utf-8-sig", newline="") as stream:
                    self.assertEqual(list(csv.reader(stream)), [
                        ["student_id", "student_name", "course_percent", "current_percent"],
                        ["s1", "Анна, В.", course, current],
                        ["s2", "Борис", "0.00", ""],
                    ])
