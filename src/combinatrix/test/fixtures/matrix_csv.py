import os, json, codecs
from combinatrix.testintegration import rel2abs
from combinatrix.core import load_matrix

class MatrixCSVFactory(object):

    @classmethod
    def get_matrix(cls, ident):
        if ident is None or ident == "-":
            return None
        path = rel2abs(__file__, "..", "resources", "fixtures", ident + ".matrix.csv")
        if os.path.exists(path):
            return load_matrix(path)
        return None