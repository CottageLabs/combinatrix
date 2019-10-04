import unittest, os
from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets, rel2abs
from combinatrix.core import CombinatrixException
from combinatrix.test.fixtures.settings_bundle import SettingsBundleFactory

EXCEPTIONS = {
    "CombinatrixException": CombinatrixException
}

BUNDLE_PATHS = {
    "none": None,
    "not_exists": rel2abs(__file__, "path", "does", "not", "exist"),
    "exists": rel2abs(__file__, "..", "resources", "fixtures", "test_bundle")
}

BUNDLE_NAMES = {
    "none": None,
    "not_exists": "not_exists",
    "exists": "test_bundle"
}

NAME_FIELDS = {
    "none": None,
    "not_exists": "not_exists",
    "exists": "test_id"
}

FILTERS = {
    "none": None,
    "single_filter": {"test_id": ["1"]},
    "double_filter": {"test_id": ["1", "2", "3"], "field3": ["1"]}
}


def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "resources", "bundles", "load_parameter_sets"),
                               "load_parameter_sets", "test_id", {"test_id": []})


class TestLoadParameterSets(unittest.TestCase):

    def setUp(self):
        super(TestLoadParameterSets, self).setUp()

    def tearDown(self):
        SettingsBundleFactory.tear_down_bundle()
        super(TestLoadParameterSets, self).tearDown()

    @parameterized.expand(load_cases)
    def test_load_parameter_sets(self, name, kwargs):
        bundle_path_arg = kwargs.get("bundle_path")
        bundle_name_arg = kwargs.get("bundle_name")
        name_field_arg = kwargs.get("name_field")
        filters_arg = kwargs.get("filters")
        settings_csv_arg = kwargs.get("settings_csv")
        settings_json_arg = kwargs.get("settings_json")
        matrix_arg = kwargs.get("matrix")
        settings_csv_age_arg = kwargs.get("settings_csv_age")
        settings_json_age_arg = kwargs.get("settings_json_age")
        matrix_age_arg = kwargs.get("matrix_age")
        raises_arg = kwargs.get("raises")

        raises = EXCEPTIONS.get(raises_arg)
        bundle_path = BUNDLE_PATHS[bundle_path_arg]
        bundle_name = BUNDLE_NAMES[bundle_name_arg]
        name_field = NAME_FIELDS[name_field_arg]
        filters = FILTERS[filters_arg]

        modified_order = {}
        if settings_csv_age_arg not in ["-"]:
            modified_order[int(settings_csv_age_arg)] = "settings_csv"
        if settings_json_age_arg not in ["-"]:
            modified_order[int(settings_json_age_arg)] = "settings_json"
        if matrix_age_arg not in ["-"]:
            modified_order[int(matrix_age_arg)] = "matrix"
        order_spec = list(modified_order.keys())
        order_spec.sort()
        order = []
        for o in order_spec:
            order.append(modified_order[o])

        bundle_info = SettingsBundleFactory.make_bundle(settings_csv_arg, settings_json_arg, matrix_arg, order)

        if raises is not None:
            with self.assertRaises(raises):
                load_parameter_sets(bundle_path, bundle_name, name_field, filters)
        else:
            combinations = load_parameter_sets(bundle_path, bundle_name, name_field, filters)

            # categorise the files into the three types:
            # 1. forward files - they should exist and have new modified dates
            # 2. current - it should exist and have an unmodified date
            # 3. past - may exist or not, and if exists should have an unmodified date
            forward = []
            current = None
            past = []

            # seek through the ordered items, looking for the item that we would expect to be
            # the one the run picks up on as the primary artefact.  This will be the earliest present
            # file
            seek = ["settings_csv", "settings_json", "matrix"]
            for o in seek:
                if bundle_info[o]["status"] == "present":
                    current = o
                    break

            # sort the list of possible files into past and forward
            mode = "past"
            for stage in seek:
                if stage == current:
                    mode = "forward"
                    continue
                if mode == "past":
                    past.append(stage)
                elif mode == "forward":
                    forward.append(stage)

            # now run the checks on each of these bins
            for p in past:
                assert not os.path.exists(bundle_info[p]["path"])

            assert os.path.exists(bundle_info[current]["path"])
            mtime = os.path.getmtime(bundle_info[current]["path"])
            assert mtime == bundle_info[current]["mtime"]

            for f in forward:
                assert os.path.exists(bundle_info[f]["path"])
                mtime = os.path.getmtime(bundle_info[f]["path"])
                assert mtime > bundle_info[f]["mtime"]

            if filters_arg == "none":
                assert len(combinations) == 8
            elif filters_arg == "single_filter":
                assert len(combinations) == 1
            elif filters_arg == "double_filter":
                assert len(combinations) == 2
