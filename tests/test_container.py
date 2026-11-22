import unittest

from pos.container import Container


class ContainerTests(unittest.TestCase):
    def test_facades_share_gradebook_state_only_within_their_session(self):
        session = Container()
        writer = session.assessments()
        writer.add_student("s1", "Анна")
        writer.add_criterion("project", "Проект", 10, 1)

        reader = session.assessments()
        self.assertEqual([criterion.id for criterion in reader.criteria()], ["project"])
        reader.set_score("s1", "project", 8)
        self.assertEqual(writer.result("s1").course_total, 80)

        other_session = Container().assessments()
        self.assertEqual(other_session.students(), [])
        self.assertEqual(other_session.criteria(), ())
