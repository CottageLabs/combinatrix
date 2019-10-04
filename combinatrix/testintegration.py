import os
from combinatrix.core import fromcsv, fromjsonfile, load_matrix, CombinatrixException


def load_parameter_sets(bundle_path, bundle_name, name_field, filters=None, newer_than_tolerance=5.0):
    if bundle_path is None:
        raise CombinatrixException("You must supply a bundle_path")
    if bundle_name is None:
        raise CombinatrixException("You must supply a bundle_name")
    if name_field is None:
        raise CombinatrixException("You must supply a name_field")

    source_csv = os.path.join(bundle_path, bundle_name + ".settings.csv")
    source_json = os.path.join(bundle_path, bundle_name + ".settings.json")
    matrix_csv = os.path.join(bundle_path, bundle_name + ".matrix.csv")

    parameters = None

    if os.path.exists(source_csv):
        parameters = fromcsv(source_csv, matrix_csv, source_json)
    elif os.path.exists(source_json):
        parameters = fromjsonfile(source_json, matrix_csv)
    elif os.path.exists(matrix_csv):
        parameters = load_matrix(matrix_csv)

    """
    source_csv_mod = None
    if os.path.exists(source_csv):
        source_csv_mod = os.path.getmtime(source_csv)

    source_json_mod = None
    if os.path.exists(source_json):
        source_json_mod = os.path.getmtime(source_json)

    matrix_csv_mod = None
    if os.path.exists(matrix_csv):
        matrix_csv_mod = os.path.getmtime(matrix_csv)


    parameters = None

    if source_csv_mod is not None:
        if source_json_mod is not None and source_json_mod > source_csv_mod + newer_than_tolerance:
            raise CombinatrixException("Both CSV and JSON settings are present, and the JSON is newer than the CSV")
        if matrix_csv_mod is not None and matrix_csv_mod > source_csv_mod + newer_than_tolerance:
            raise CombinatrixException("Both CSV and Matrix are present, and the matrix is newer than the CSV")

        parameters = fromcsv(source_csv, matrix_csv, source_json)

    if parameters is None:
        if source_json_mod is not None:
            if matrix_csv_mod is not None and matrix_csv_mod > source_json_mod + newer_than_tolerance:
                raise CombinatrixException("Both JSON and Matrix are present, and the matrix is newer than the CSV")

            parameters = fromjsonfile(source_json, matrix_csv)

    if matrix_csv_mod is not None:
        parameters = load_matrix(matrix_csv)
    """

    if parameters is None:
        raise CombinatrixException("No viable build approach for bundle " + bundle_name + " at " + bundle_path)

    # check that the name field we've been given exists
    for p in parameters:
        if p.get(name_field) is None:
            raise CombinatrixException("At least one record does not contain the name_field")

    if filters is None:
        return [(p[name_field], p) for p in parameters]

    filtered = []
    for p in parameters:
        counter = 0
        for field, allowed_values in filters.items():
            if len(allowed_values) == 0:
                counter += 1
            elif p[field] in allowed_values:
                counter += 1
        if counter == len(list(filters.keys())):
            filtered.append((p[name_field], p))

    return filtered


def rel2abs(file, *args):
    file = os.path.realpath(file)
    if os.path.isfile(file):
        file = os.path.dirname(file)
    return os.path.abspath(os.path.join(file, *args))
