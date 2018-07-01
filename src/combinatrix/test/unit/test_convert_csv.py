import unittest, os
from parameterized import parameterized
from testintegration import load_parameter_sets, rel2abs
from combinatrix.core import CombinatrixException, convert_csv
from combinatrix.test.fixtures.settings_csv import SettingsCSVFactory
from combinatrix.test.fixtures.settings_json import SettingsJSONFactory

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "resources", "bundles", "convert_csv"), "convert_csv", "test_id", {"test_id" : []})

EXCEPTIONS = {
    "CombinatrixException" : CombinatrixException
}

CSV_PATHS = {
    "none" : None,
    "missing" : rel2abs(__file__, "path", "does", "not", "exist.csv")
}

PARAMS_OUT_PATHS = {
    "none" : None,
    "missing_dir" : rel2abs(__file__, "path", "does", "not", "exist"),
    "available" : rel2abs(__file__, "..", "resources", "tmp", "test_convert_csv.csv")
}

class TestConvertCsv(unittest.TestCase):

    def setUp(self):
        super(TestConvertCsv, self).setUp()

    def tearDown(self):
        super(TestConvertCsv, self).tearDown()

    @parameterized.expand(load_cases)
    def test_convert_csv(self, name, kwargs):
        csv_path_arg = kwargs.get("csv_path")
        params_out_path_arg = kwargs.get("params_out_path")
        csv_state_arg = kwargs.get("csv_state")
        compare_params_arg = kwargs.get("compare_params")
        raises_arg = kwargs.get("raises")

        csv_path = CSV_PATHS.get(csv_path_arg)
        if csv_path is None:
            csv_path = SettingsCSVFactory.get_csv_path(csv_state_arg)
        params_out_path = PARAMS_OUT_PATHS[params_out_path_arg]
        raises = EXCEPTIONS.get(raises_arg)

        if raises is not None:
            with self.assertRaises(raises):
                convert_csv(csv_path, params_out_path)
        else:
            parameters = convert_csv(csv_path, params_out_path)

            if params_out_path_arg in ["available"]:
                assert os.path.exists(params_out_path)

            if compare_params_arg in ["good_1"]:
                compare_with_json = SettingsJSONFactory.get_json(compare_params_arg)
                assert parameters == compare_with_json


