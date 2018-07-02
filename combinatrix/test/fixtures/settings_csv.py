import os
from combinatrix.testintegration import rel2abs

class SettingsCSVFactory(object):

    @classmethod
    def get_csv_path(cls, ident):
        path = rel2abs(__file__, "..", "resources", "fixtures", ident + ".settings.csv")
        if os.path.exists(path):
            return path
        return None