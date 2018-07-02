import codecs, json, os
from combinatrix import csvutil

INDEX = "index"
GENERATED = "generated"
CONDITIONAL = "conditional"

FIELD = "field"
TYPE = "type"
DEFAULT = "default"
VALUES = "values"
CONSTRAINT = "constraint"
CONDITION = "condition"

ANY = "*"

class CombinatrixException(Exception):
    pass


def convert_csv(csv_path, params_out_path=None):
    if csv_path is None:
        raise CombinatrixException("You must specify a csv_path to convert")
    parameters = _csv2parameters(csv_path)
    if params_out_path is not None:
        if not os.path.exists(os.path.dirname(params_out_path)):
            raise CombinatrixException("The directory for the params_out_path does not exist")
        with codecs.open(params_out_path, "wb", "utf-8") as f:
            f.write(json.dumps(parameters, indent=2))
    return parameters


def _csv2parameters(csv_path):
    if not os.path.exists(csv_path) or os.path.isdir(csv_path):
        raise CombinatrixException("csv_path is set to a missing file or to a directory")
    with codecs.open(csv_path, "rb", "utf-8") as f:
        reader = csvutil.UnicodeReader(f)

        parameters = []
        try:
            first = reader.next()
        except StopIteration:
            raise CombinatrixException("Empty settings csv")
        except UnicodeDecodeError as e:
            raise CombinatrixException(e)

        if first[0] != FIELD:
            raise CombinatrixException("First CSV row must be a 'field' row")
        for i in range(1, len(first)):
            obj = {"name" : first[i]}
            parameters.append(obj)

        for row in reader:
            if row[0] == "":
                continue
            elif row[0] == TYPE:
                _read_types(row[1:], parameters)
            elif row[0] == DEFAULT:
                _read_defaults(row[1:], parameters)
            elif row[0] == VALUES:
                _read_values(row[1:], parameters)
            elif row[0].startswith(CONSTRAINT):
                key = row[0].split(" ", 1)[1].strip()
                _read_constraint(row[1:], key, parameters)
            elif row[0].startswith(CONDITION):
                key = row[0].split(" ", 1)[1].strip()
                _read_condition(row[1:], key, parameters)

    return {"parameters" : parameters}


def _read_types(type_list, parameters):
    for i in range(len(type_list)):
        t = type_list[i]
        parameters[i]["type"] = t
        # if this is not a conditional type, and the default has already
        # been set, then remove it, it's not needed
        if t != "conditional" and "default" in parameters[i]:
            del parameters[i]["default"]


def _read_defaults(default_list, parameters):
    for i in range(len(default_list)):
        d = default_list[i]
        # set the default if the type is conditional, or no type is currently set
        if parameters[i].get("type", "conditional") == "conditional":
            parameters[i]["default"] = d

def _read_values(value_list, parameters):
    for i in range(len(value_list)):
        v = value_list[i]
        if v == "":
            continue
        if "values" not in parameters[i]:
            parameters[i]["values"] = {}
        if v not in parameters[i]["values"]:
            parameters[i]["values"][v] = {}


def _read_constraint(constraint_set, field, parameters):
    headers = [p["name"] for p in parameters]
    key_idx = headers.index(field)
    key_value = None

    # work out the value and the set of constraints for the supplied field which are specified by this row
    constraint_map = {}
    for i in range(len(constraint_set)):
        constraint = constraint_set[i]
        if constraint == "" or constraint == ANY:
            continue

        if i == key_idx:
            key_value = constraint
        else:
            constraint_map[headers[i]] = [constraint]

    if len(constraint_map.keys()) == 0:
        return

    # get the field configuration from the parameters, to which we need to add the latest knowledge
    # from this row
    field_cfg = None
    for p in parameters:
        if p.get("name") == field:
            field_cfg = p
            break

    if "values" not in field_cfg:
        field_cfg["values"] = {}
    if key_value not in field_cfg["values"]:
        field_cfg["values"][key_value] = {}
    if "constraints" not in field_cfg["values"][key_value]:
        field_cfg["values"][key_value]["constraints"] = {}
    context = field_cfg["values"][key_value]["constraints"]

    for key, values in constraint_map.iteritems():
        if key not in context:
            context[key] = values
        else:
            context[key] += values


def _read_condition(condition_set, field, parameters):
    headers = [p["name"] for p in parameters]
    key_idx = headers.index(field)
    key_value = None

    # work out the value and the set of constraints for the supplied field which are specified by this row
    condition_map = {}
    for i in range(len(condition_set)):
        condition = condition_set[i]
        if condition == "" or condition == ANY:
            continue

        if i == key_idx:
            key_value = condition
        else:
            condition_map[headers[i]] = [condition]

    if len(condition_map.keys()) == 0:
        return

    # get the field configuration from the parameters, to which we need to add the latest knowledge
    # from this row
    field_cfg = None
    for p in parameters:
        if p.get("name") == field:
            field_cfg = p
            break

    if "values" not in field_cfg:
        field_cfg["values"] = {}
    if key_value not in field_cfg["values"]:
        field_cfg["values"][key_value] = {}
    if "conditions" not in field_cfg["values"][key_value]:
        field_cfg["values"][key_value]["conditions"] = []

    field_cfg["values"][key_value]["conditions"].append(condition_map)



def fromcsv(csv_path, combos_out_path=None, params_out_path=None):
    parameters = convert_csv(csv_path, params_out_path)
    return combine(parameters, combos_out_path)


def fromjsonfile(json_path, out_path):
    with codecs.open(json_path, "rb", "utf-8") as f:
        j = json.loads(f.read())
    return combine(j, out_path)


def combine(parameters, out_path):
    # validate the input
    if parameters is None or out_path is None:
        raise CombinatrixException("parameters and out_path must be set")

    out_dir = os.path.dirname(out_path)
    if not os.path.exists(out_dir):
        raise CombinatrixException("Directory {x} does not exist for output path".format(x=out_dir))

    # get all the fields that we're going to use to generate the first set
    # this is the list of field names where the type is "generate" (or not set)
    fields = [p for p in parameters.get("parameters", []) if p.get("type", GENERATED) == GENERATED]

    # create a counter for each field we're going to generate.  This will be used to help us track the
    # generation of a complete coverage dataset
    # the counter is max is the number of values for each generateable field
    counters = {}
    for f in fields:
        counters[f.get("name")] = { "current" : 0, "max" : len(f.get("values").keys()) - 1 }
        # at the same time, for convenience, create a set of keys that are arbitrarily ordered
        # so that we can iterate over them consistently later
        f["ordered_values"] = f.get("values").keys()

    # now generate a complete set of possible combinations of all values for all fields
    combinations = []
    combinations.append(_generate_current(fields, counters))
    while True:
        counted = _count(fields, counters)
        if not counted:
            break
        combinations.append(_generate_current(fields, counters))

    # get all the fields which are populated conditionally
    conditionals = [p for p in parameters.get("parameters", []) if p.get("type", GENERATED) == CONDITIONAL]

    # get all the fields which are index fields
    indices = [p for p in parameters.get("parameters", []) if p.get("type", GENERATED) == INDEX]
    current_index = 1

    # now filter the complete list, to take into account any field constraints
    # Also add any conditional fields to the combination
    final = []
    for combo in combinations:
        if _filter(combo, fields):
            _add_conditionals(combo, conditionals)
            current_index = _add_index(combo, indices, current_index)
            final.append(combo)

    if out_path:
        header = [p.get("name") for p in parameters.get("parameters", [])]
        with codecs.open(out_path, "wb", "utf-8") as f:
            writer = csvutil.UnicodeWriter(f)
            writer.writerow(header)
            for combo in final:
                row = [unicode(combo.get(field.get("name"), "")) for field in parameters.get("parameters", [])]
                writer.writerow(row)

    return final


def _generate_current(fields, counters):
    """
    For each field, select the value from the "ordered_values" array which corresponds with
    where the counter for that field currently points
    :param fields:
    :param counters:
    :return:
    """
    record = {}
    for field in fields:
        name = field.get("name")
        current = counters[name]["current"]
        record[name] = field["ordered_values"][current]
    return record


def _count(fields, counters):
    counted = False
    for i in range(len(fields) - 1, -1, -1):
        field = fields[i].get("name")
        current = counters[field]["current"]
        if current == counters[field]["max"]:
            counters[field]["current"] = 0
        else:
            counters[field]["current"] += 1
            counted = True
            break

    return counted


def _filter(combo, fields):
    for filter in fields:
        cval = combo[filter["name"]]
        constraints = filter.get("values", {}).get(cval, {}).get("constraints", {})
        if (len(constraints.keys())) == 0:
            continue
        for cfield, values in constraints.iteritems():
            if combo[cfield] not in values:
                return False
    return True


def _add_conditionals(combo, conditionals):
    for field in conditionals:
        for val, conditions in field.get("values", {}).iteritems():
            tripped = False
            if "conditions" not in conditions:
                continue
            for match_group in conditions["conditions"]:
                trips = 0
                for other_field, other_values in match_group.iteritems():
                    if combo[other_field] in other_values:
                        trips += 1
                if trips == len(match_group.keys()):
                    combo[field.get("name")] = val
                    tripped = True
                    break
            if tripped:
                break
            else:
                combo[field.get("name")] = field.get("default", "")
    return


def _add_index(combo, indices, current_index):
    for field in indices:
        combo[field.get("name")] = unicode(current_index)
    return current_index + 1


def load_matrix(source_path):
    with codecs.open(source_path, "rb", "utf-8") as f:
        return [p for p in csvutil.UnicodeDictReader(f)]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--csv", help="input csv")
    parser.add_argument("-j", "--json", help="input json")
    parser.add_argument("-o", "--out", help="output csv file")
    parser.add_argument("-p", "--pout", help="output parameters json file")
    parser.add_argument("-g", "--generate", help="should the combinations be generated")

    args = parser.parse_args()

    if args.csv and args.json:
        print("Specify either -c/--csv or -j/--json, but not both")
        exit()

    if not args.csv and not args.json:
        print("Specify either -c/--csv or -j/--json")
        exit()

    if not args.out:
        print("You must specify an output file with -o")
        exit()

    gen = False
    if args.generate:
        gen = True

    if args.csv and not gen:
        convert_csv(args.csv, args.pout)
    elif args.csv and gen:
        fromcsv(args.csv, args.out, args.pout)
    elif args.json and gen:
        fromjsonfile(args.json, args.out)
