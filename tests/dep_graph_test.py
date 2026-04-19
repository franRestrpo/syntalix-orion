import unittest
from ui.textual_prototype.dep_graph import DependencyGraph


class TestDependencyGraph(unittest.TestCase):
    def test_basic_structure(self):
        g = DependencyGraph()
        deps = g.get_deployments()
        self.assertIsInstance(deps, list)
        self.assertEqual(len(deps), 4)

    def test_plan_generation(self):
        g = DependencyGraph()
        plan = g.get_plan("Apps")
        self.assertIn("Deployment Plan for Apps:", plan)


if __name__ == "__main__":
    unittest.main()
