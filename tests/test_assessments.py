import csv
import unittest
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory

from pos.container import Container


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.app = Container().assessments()
        self.app.add_student("s1", "Анна")

    def test_correcting_one_namesakes_score_preserves_the_others(self):
        self.app.add_student("s2", "Анна")
        self.app.add_criterion("project", "Проект", 10, 1)
        self.app.set_score("s1", "project", 8)
        self.app.set_score("s2", "project", 6)

        self.app.set_score("s1", "project", 9)

        self.assertEqual(self.app.result("s1").course_total, 90)
        self.assertEqual(self.app.result("s2").course_total, 60)

    def test_adding_a_criterion_recalculates_only_the_course_total(self):
        self.app.add_criterion("project", "Проект", 10, 3)
        self.app.set_score("s1", "project", 8)
        before = self.app.result("s1")
        self.assertEqual((before.course_total, before.current_result), (80, 80))

        self.app.add_criterion("exam", "Защита", 5, 1)

        after = self.app.result("s1")
        self.assertEqual((after.course_total, after.current_result), (60, 80))

    def test_csv_rounds_repeating_percentages_only_at_export(self):
        self.app.add_criterion("project", "Проект", 3, 1)
        self.app.add_criterion("exam", "Защита", 3, 1)
        self.app.set_score("s1", "project", 2)

        result = self.app.result("s1")
        self.assertEqual(result.course_total, Fraction(100, 3))
        self.assertEqual(result.current_result, Fraction(200, 3))

        with TemporaryDirectory() as directory:
            path = Path(directory) / "results.csv"
            self.app.export_results(path)
            with path.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["student_id"], "s1")
        self.assertEqual(rows[0]["course_percent"], "33.33")
        self.assertEqual(rows[0]["current_percent"], "66.67")
