import unittest
from fractions import Fraction

from pos.domain import (
    CourseTotal, CurrentResult, DomainError, FinalScoreCalculator, GradebookEntry,
    Rubric, ScoreOutOfRange, Student,
)


class StudentTests(unittest.TestCase):
    def test_identity_depends_only_on_student_id(self):
        original = Student("s1", "Анна")
        renamed = Student("s1", "Анна Иванова")
        namesake = Student("s2", "Анна")

        self.assertEqual(original, renamed)
        self.assertNotEqual(original, namesake)
        self.assertEqual({original: "s1"}[renamed], "s1")


class GradebookTests(unittest.TestCase):
    def setUp(self):
        self.rubric = Rubric()
        self.rubric.add_criterion("project", "Проект", 10, 3)
        self.entry = GradebookEntry(Student("s1", "Анна"), self.rubric)

    def test_invalid_correction_preserves_previous_score(self):
        self.entry.set_score("project", 8)

        with self.assertRaises(ScoreOutOfRange):
            self.entry.set_score("project", 12)

        self.assertEqual(self.entry.get_score("project"), 8)

    def test_each_entry_uses_its_own_rubric_for_grading_and_totals(self):
        other_rubric = Rubric()
        other_rubric.add_criterion("project", "Проект", 20, 1)
        other_entry = GradebookEntry(self.entry.student, other_rubric)
        calculator = FinalScoreCalculator(CourseTotal())

        self.entry.set_score("project", 8)
        other_entry.set_score("project", 20)
        with self.assertRaises(ScoreOutOfRange):
            self.entry.set_score("project", 20)

        self.assertEqual(calculator.calculate(self.entry), 80)
        self.assertEqual(calculator.calculate(other_entry), 100)

    def test_unknown_criterion_is_rejected(self):
        with self.assertRaises(DomainError):
            self.entry.set_score("exam", 3)
        self.assertIsNone(self.entry.get_score("exam"))

    def test_allowed_score_boundaries(self):
        for score in (0, 10):
            self.entry.set_score("project", score)
            self.assertEqual(self.entry.get_score("project"), score)
        with self.assertRaises(ScoreOutOfRange):
            self.entry.set_score("project", -1)

    def test_rubric_rejects_duplicate_and_invalid_criteria(self):
        for key, maximum, weight in [("project", 20, 1), ("exam", 0, 1), ("exam", 5, 0)]:
            with self.subTest(key=key, maximum=maximum, weight=weight), self.assertRaises(DomainError):
                self.rubric.add_criterion(key, "Защита", maximum, weight)
        self.assertEqual([c.max_score for c in self.rubric.criteria()], [10])

    def test_weighted_scores_after_correction_and_cancellation(self):
        course = FinalScoreCalculator(CourseTotal())
        current = FinalScoreCalculator(CurrentResult())
        self.rubric.add_criterion("exam", "Защита", 5, Fraction(1))
        self.entry.set_score("project", 8)
        self.entry.set_score("exam", 3)
        self.assertEqual(course.calculate(self.entry), 75)
        self.entry.set_score("exam", 0)
        self.assertEqual(current.calculate(self.entry), 60)
        self.entry.cancel_score("exam")
        self.assertEqual(course.calculate(self.entry), 60)
        self.assertEqual(current.calculate(self.entry), 80)

    def test_empty_rubric_and_no_evaluations(self):
        course = FinalScoreCalculator(CourseTotal())
        current = FinalScoreCalculator(CurrentResult())
        empty_entry = GradebookEntry(self.entry.student, Rubric())
        self.assertIsNone(course.calculate(empty_entry))
        self.assertEqual(course.calculate(self.entry), 0)
        self.assertIsNone(current.calculate(self.entry))
