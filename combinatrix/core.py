import json, os, csv
from combinatrix import models, constants
from combinatrix.exceptions import CombinatrixException, ValidationException


def convert_csv(csv_path, params_out_path=None):
    if csv_path is None:
        raise CombinatrixException("You must specify a csv_path to convert")
    parameters = _csv2parameters(csv_path)
    if params_out_path is not None:
        dir = os.path.dirname(params_out_path)
        if dir == "":                                          # we were just given a filename for the current directory
            dir = "."
        if not os.path.exists(dir):
            raise CombinatrixException("The directory for the params_out_path does not exist")
        with open(params_out_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(parameters.as_dict(), indent=2))
    return parameters


def _csv2parameters(csv_path):
    if not os.path.exists(csv_path) or os.path.isdir(csv_path):
        raise CombinatrixException("csv_path is set to a missing file or to a directory")
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)

        parameters = models.Parameters()
        try:
            first = next(reader)
            second = next(reader)
        except StopIteration:
            raise CombinatrixException("Empty settings csv")
        except UnicodeDecodeError as e:
            raise CombinatrixException(e)

        if first[0] != constants.FIELD:
            raise CombinatrixException("First CSV row must be a 'field' row")
        if second[0] != constants.TYPE:
            raise CombinatrixException("Second CSV row must be a 'type' row")

        for i in range(1, len(first)):
            parameters.add_field(first[i], second[i])

        for row in reader:
            if row[0] == "":
                continue
            elif row[0] == constants.DEFAULT:
                _read_defaults(row[1:], parameters)
            elif row[0] == constants.VALUES:
                _read_values(row[1:], parameters)
            elif row[0].startswith(constants.CONSTRAINT):
                key = row[0].split(" ", 1)[1].strip()
                _read_constraint(row[1:], key, parameters)
            elif row[0].startswith(constants.CONDITION):
                key = row[0].split(" ", 1)[1].strip()
                _read_condition(row[1:], key, parameters)

    return parameters


def _read_defaults(default_list, parameters):
    for i in range(len(default_list)):
        parameters.set_default(i, default_list[i])


def _read_values(value_list, parameters):
    for i in range(len(value_list)):
        parameters.add_value(i, value_list[i])


def _read_constraint(constraint_set, field, parameters):
    headers = parameters.field_names()
    key_idx = headers.index(field)
    key_value = None

    # work out the value and the set of constraints for the supplied field which are specified by this row
    constraint_map = {}
    for i in range(len(constraint_set)):
        if parameters.get(i).get("type") not in [constants.GENERATED]:
            continue

        constraint = constraint_set[i]
        if constraint in constants.ANY:
            continue

        if i == key_idx:
            key_value = constraint
        else:
            constraint = constraint.strip()
            is_not = False
            if constraint.startswith(constants.NOT):
                is_not = True
                constraint = constraint[1:]
            bits = constraint.split(constants.OR)
            bits = [b.strip() for b in bits]

            if is_not:
                if headers[i] not in constraint_map:
                    constraint_map[headers[i]] = {}
                constraint_map[headers[i]]["nor"] = bits
            else:
                if headers[i] not in constraint_map:
                    constraint_map[headers[i]] = {}
                constraint_map[headers[i]]["or"] = bits

    # if we didn't find any constraints no need to go any further
    if len(list(constraint_map.keys())) == 0:
        return

    for other_field, rules in constraint_map.items():
        parameters.add_constraint(field, key_value, other_field, or_values=rules.get("or"), nor_values=rules.get("nor"))


def _read_condition(condition_set, field, parameters):
    headers = parameters.field_names()
    key_idx = headers.index(field)
    key_value = None

    # work out the value and the set of constraints for the supplied field which are specified by this row
    condition_map = {}
    for i in range(len(condition_set)):
        if parameters.get(i).get("type") not in [constants.GENERATED, constants.CONDITIONAL]:
            continue

        condition = condition_set[i]
        if condition in constants.ANY:
            continue

        if i == key_idx:
            key_value = condition
        else:
            condition = condition.strip()
            is_not = False
            if condition.startswith(constants.NOT):
                is_not = True
                condition = condition[1:]
            bits = condition.split(constants.OR)
            bits = [b.strip() for b in bits]

            if is_not:
                if headers[i] not in condition_map:
                    condition_map[headers[i]] = {}
                condition_map[headers[i]]["nor"] = bits
            else:
                if headers[i] not in condition_map:
                    condition_map[headers[i]] = {}
                condition_map[headers[i]]["or"] = bits

    if len(list(condition_map.keys())) == 0:
        return

    parameters.add_condition_set(field, key_value, condition_map)


def fromcsv(csv_path, combos_out_path, params_out_path=None):
    parameters = convert_csv(csv_path, params_out_path)
    return combine(parameters, combos_out_path)


def fromjsonfile(json_path, out_path):
    with open(json_path, "r", encoding="utf-8") as f:
        j = json.loads(f.read())
    return combine(j, out_path)


def combine(parameters, out_path):
    # validate the input
    if parameters is None or out_path is None:
        raise CombinatrixException("parameters and out_path must be set")

    if not isinstance(parameters, models.Parameters):
        parameters = models.Parameters(parameters)

    out_dir = os.path.dirname(out_path)
    if out_dir == "":   # we have been given a filename in the current directory
        out_dir = "."
    if not os.path.exists(out_dir):
        raise CombinatrixException("Directory {x} does not exist for output path".format(x=out_dir))

    # construct the counter around the parameters
    counter = models.ComboIterator(parameters)

    # get all the generated fields
    generated_fields = parameters.field_names(types=[constants.GENERATED])

    # get all the fields which are populated conditionally
    conditional_fields = parameters.field_names(types=[constants.CONDITIONAL])

    # get all the fields which are index fields
    index_fields = parameters.field_names(types=[constants.INDEX])
    current_index = 1

    # iterate through all allowable combinations, and construct the final combo set
    combinations = []
    while next(counter):
        combo = _generate_current(generated_fields, parameters, counter)
        _add_conditionals(combo, conditional_fields, parameters)
        current_index = _add_index(combo, current_index, index_fields, parameters)
        combinations.append(combo)

    if out_path:
        header = parameters.field_names()
        with open(out_path, "w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for combo in combinations:
                row = [str(combo.get(name, "")) for name in header]
                writer.writerow(row)

    return combinations


def _generate_current(fields, parameters, counter):
    """
    For each field, select the value from the list of values (which are consistently ordered)
    that corresponds to the current counter position
    :param fields:
    :param counter:
    :return:
    """
    record = {}
    for name in fields:
        values = parameters.get_values(name)
        current = counter.get_current(name)
        record[name] = values[current]
    return record


def _filter(combo, fields, parameters):
    for name in fields:
        cval = combo[name]
        constraints = parameters.get_constraints(name, cval)
        if (len(list(constraints.keys()))) == 0:
            continue

        for cfield, ors_and_nors in constraints.items():
            if "or" in ors_and_nors and "nor" in ors_and_nors:
                raise CombinatrixException("You cannot define both 'or' and 'nor' in your constraints")

            if "or" in ors_and_nors:
                if combo[cfield] not in ors_and_nors["or"]:
                    return False
            if "nor" in ors_and_nors:
                if combo[cfield] in ors_and_nors["nor"]:
                    return False

    return True


def _add_conditionals(combo, fields, parameters):
    for name in fields:
        possible_values = []
        values = parameters.get_values(name)
        for val in values:
            conditions = parameters.get_conditions(name, val)
            if conditions is None:
                continue
            for match_group in conditions:
                if _conditions_match(combo, match_group):
                    possible_values.append(val)
                    break

            """
            for match_group in conditions:
                trips = 0
                for other_field, other_values in match_group.iteritems():
                    if combo[other_field] in other_values:
                        trips += 1
                if trips == len(match_group.keys()):
                    possible_values.append(val)
                    break
            """

        possible_values = list(set(possible_values))
        if len(possible_values) == 0:
            combo[name] = parameters.get_default(name)
        elif len(possible_values) == 1:
            combo[name] = possible_values[0]
        else:
            raise CombinatrixException("More than one possible value for '{x}'.  For combination: {y} the possible values are: {z}".format(
                                                x=name, y=combo, z=possible_values))
    return


def _conditions_match(combo, match_group):
    trips = 0
    for other_field, match_conditions in match_group.items():
        if "or" in match_conditions:
            if combo[other_field] in match_conditions.get("or", []):
                trips += 1
        elif "nor" in match_conditions:
            if combo[other_field] not in match_conditions.get("nor", []):
                trips += 1
        else:
            raise ValidationException("Expected 'or' or 'nor' in match group")
    return trips == len(list(match_group.keys()))


def _add_index(combo, current_index, indices, parameters):
    for name in indices:
        combo[name] = str(current_index)
    return current_index + 1


def load_matrix(source_path):
    with open(source_path, "r", encoding="utf-8") as f:
        return [p for p in csv.DictReader(f)]
