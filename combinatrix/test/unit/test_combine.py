import unittest, os
from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets, rel2abs
from combinatrix.core import CombinatrixException, combine, load_matrix
from combinatrix.test.fixtures.matrix_csv import MatrixCSVFactory
from combinatrix.test.fixtures.settings_json import SettingsJSONFactory

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "resources", "bundles", "combine"), "combine", "test_id",
                               {"test_id" : []})

EXCEPTIONS = {
    "CombinatrixException" : CombinatrixException
}

OUT_PATHS = {
    "none" : None,
    "missing_dir" : rel2abs(__file__, "path", "does", "not", "exist"),
    "available" : rel2abs(__file__, "..", "resources", "tmp", "combine.matrix.csv")
}

class TestCombine(unittest.TestCase):

    def setUp(self):
        super(TestCombine, self).setUp()

    def tearDown(self):
        available = OUT_PATHS["available"]
        if os.path.exists(available):
            os.remove(available)

        super(TestCombine, self).tearDown()

    @parameterized.expand(load_cases)
    def test_combine(self, name, kwargs):
        parameters_arg = kwargs.get("parameters")
        out_path_arg = kwargs.get("out_path")
        check_matrix_arg = kwargs.get("check_matrix")
        raises_arg = kwargs.get("raises")

        raises = EXCEPTIONS.get(raises_arg)
        parameters = SettingsJSONFactory.get_json(parameters_arg)
        out_path = OUT_PATHS.get(out_path_arg)

        if raises is not None:
            with self.assertRaises(raises):
                combine(parameters, out_path)
        else:
            combinations = combine(parameters, out_path)

            from_file = None
            if out_path_arg in ["available"]:
                assert os.path.exists(out_path)
                from_file = load_matrix(out_path)

            matrix = MatrixCSVFactory.get_matrix(check_matrix_arg)

            assert combinations == matrix
            assert combinations == from_file


