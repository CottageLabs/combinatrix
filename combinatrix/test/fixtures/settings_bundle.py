import os, shutil
from combinatrix.testintegration import rel2abs


class SettingsBundleFactory(object):

    @classmethod
    def make_bundle(cls, settings_csv, settings_json, matrix, modified_order):
        fixtures = rel2abs(__file__, "..", "resources", "fixtures")
        bundle = rel2abs(__file__, "..", "resources", "fixtures", "test_bundle")

        bundle_info = {
            "settings_csv": {
                "path": None,
                "mtime": -1,
                "status": settings_csv
            },
            "settings_json": {
                "path": None,
                "mtime": -1,
                "status": settings_json
            },
            "matrix": {
                "path": None,
                "mtime": -1,
                "status": matrix
            }
        }

        target = os.path.join(bundle, "test_bundle.settings.csv")
        bundle_info["settings_csv"]["path"] = target
        if settings_csv in ["present"] and "settings_csv" in modified_order:
            source = os.path.join(fixtures, "test_bundle.settings.csv")
            shutil.copy(source, target)
            offset = modified_order.index("settings_csv")
            mtime = (offset + 1) * 1000
            os.utime(target, (mtime, mtime))
            bundle_info["settings_csv"]["mtime"] = mtime

        target = os.path.join(bundle, "test_bundle.settings.json")
        bundle_info["settings_json"]["path"] = target
        if settings_json in ["present"] and "settings_json" in modified_order:
            source = os.path.join(fixtures, "test_bundle.settings.json")
            shutil.copy(source, target)
            offset = modified_order.index("settings_json")
            mtime = (offset + 1) * 1000
            os.utime(target, (mtime, mtime))
            bundle_info["settings_json"]["mtime"] = mtime

        target = os.path.join(bundle, "test_bundle.matrix.csv")
        bundle_info["matrix"]["path"] = target
        if matrix in ["present"] and "matrix" in modified_order:
            source = os.path.join(fixtures, "test_bundle.matrix.csv")
            shutil.copy(source, target)
            offset = modified_order.index("matrix")
            mtime = (offset + 1) * 1000
            os.utime(target, (mtime, mtime))
            bundle_info["matrix"]["mtime"] = mtime

        return bundle_info

    @classmethod
    def tear_down_bundle(cls):
        bundle = rel2abs(__file__, "..", "resources", "fixtures", "test_bundle")
        settings_csv = os.path.join(bundle, "test_bundle.settings.csv")
        settings_json = os.path.join(bundle, "test_bundle.settings.json")
        matrix = os.path.join(bundle, "test_bundle.matrix.csv")

        if os.path.exists(settings_csv):
            os.remove(settings_csv)
        if os.path.exists(settings_json):
            os.remove(settings_json)
        if os.path.exists(matrix):
            os.remove(matrix)
