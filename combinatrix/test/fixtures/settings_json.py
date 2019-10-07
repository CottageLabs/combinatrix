import os, json
from combinatrix.testintegration import rel2abs


class SettingsJSONFactory(object):

    @classmethod
    def get_json(cls, ident):
        if ident is None:
            return None
        path = rel2abs(__file__, "..", "resources", "fixtures", ident + ".settings.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.loads(f.read())
        return None
