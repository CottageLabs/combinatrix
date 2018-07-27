from combinatrix import constants

class Parameters(object):

    def __init__(self, raw=None):
        self.data = [] if raw is None else raw.get("parameters", [])
        self._index = {}
        self._value_index = {}
        self._make_index()

    def add_field(self, name, type):
        self.data.append({"name" : name, "type" : type})
        self._index[name] = len(self.data) - 1

    def set_default(self, name, default):
        obj = self.get(name)
        if obj.get("type") not in [constants.CONDITIONAL]:
            return
        obj["default"] = default

    def add_value(self, name, value):
        obj = self.get(name)
        if obj.get("type") in [constants.INDEX, constants.COMMENT]:
            return
        if value == "":
            return
        if "values" not in obj:
            obj["values"] = {}
        if value not in obj["values"]:
            obj["values"][value] = {}

        # keep an ordered list of values for iteration later
        real_name = obj.get("name")
        if real_name not in self._value_index:
            self._value_index[real_name] = []
        if value not in self._value_index[real_name]:
            self._value_index[real_name].append(value)

    def add_constraints(self, name, value, constraints):
        obj = self.get(name)
        if obj.get("type") not in [constants.GENERATED]:
            return
        self.add_value(name, value)
        if "constraints" not in obj["values"][value]:
            obj["values"][value]["constraints"] = {}
        context = obj["values"][value]["constraints"]

        for key, values in constraints.iteritems():
            if key not in context:
                context[key] = values
            else:
                if "or" not in context[key] and "or" in values:
                    context[key]["or"] = values["or"]
                elif "or" in values:
                    context[key]["or"] += values["or"]

                if "nor" not in context[key] and "nor" in values:
                    context[key]["nor"] = values["nor"]
                elif "nor" in values:
                    context[key]["nor"] += values["nor"]

    def add_conditions(self, name, value, conditions):
        obj = self.get(name)
        if obj.get("type") not in [constants.CONDITIONAL]:
            return
        self.add_value(name, value)
        if "conditions" not in obj["values"][value]:
            obj["values"][value]["conditions"] = []
        context = obj["values"][value]["conditions"]
        context.append(conditions)

    def field_names(self, types=None):
        if types is None:
            return [p["name"] for p in self.data]
        return [p["name"] for p in self.data if p["type"] in types]

    def get_default(self, name):
        return self.get(name).get("default", "")

    def get_values(self, name):
        obj = self.get(name)
        return self._value_index.get(obj.get("name"))

    def get_constraints(self, name, value):
        obj = self.get(name)
        return obj.get("values", {}).get(value, {}).get("constraints", {})

    def get_conditions(self, name, value):
        obj = self.get(name)
        return obj.get("values", {}).get(value, {}).get("conditions", [])

    def get(self, name):
        if isinstance(name, int):
            return self.data[name]
        else:
            return self.data[self._index[name]]

    def as_dict(self):
        return {"parameters" : self.data}

    def _make_index(self):
        for i, obj in enumerate(self.data):
            self._index[obj.get("name")] = i
            self._value_index[obj.get("name")] = obj.get("values", {}).keys()


class ComboIterator(object):
    def __init__(self, parameters):
        self.counters = {}
        self._index = []
        self._init = True

        generated_fields = parameters.field_names(types=[constants.GENERATED])
        for gf in generated_fields:
            values = parameters.get_values(gf)
            s = {}
            for i, value in enumerate(values):
                constraints = parameters.get_constraints(gf, value)
                skip = {}
                for field, rules in constraints.iteritems():
                    if "nor" in rules:
                        skip[field] = self._values_to_indices(parameters, field, rules["nor"])
                    elif "or" in rules:
                        skip[field] = self._mirror_to_indices(parameters, field, rules["or"])
                if len(skip.keys()) > 0:
                    s[i] = skip

            self.counters[gf] = {"c" : 0, "m": len(values) - 1, "s": s}
            self._index.append(gf)

    def _mirror_to_indices(self, parameters, field, values):
        field_values = parameters.get_values(field)
        return [field_values.index(v) for v in field_values if v not in values]

    def _values_to_indices(self, parameters, field, values):
        field_values = parameters.get_values(field)
        return [field_values.index(v) for v in values]

    def get_current(self, name):
        return self.counters[name]["c"]

    def reset_current(self, name):
        self.counters[name]["c"] = 0

    def increment_current(self, name):
        self.counters[name]["c"] += 1

    def get_max(self, name):
        return self.counters[name]["m"]

    def get_skip(self, name):
        return self.counters[name]["s"]

    def next(self):
        if self._init:
            self._init = False
            if self._check_position():
                return True

        counted = False
        while True:
            counted = False
            for i in range(len(self._index) -1, -1, -1):
                field = self._index[i]
                current = self.get_current(field)
                max = self.get_max(field)
                if current == max:
                    self.reset_current(field)
                else:
                    self.increment_current(field)
                    counted = True
                    break
            if not counted:
                break
            if self._check_position():
                break
        return counted

    def _check_position(self):
        for i in range(len(self._index)):
            field = self._index[i]
            current = self.get_current(field)
            skips = self.get_skip(field)
            if current not in skips:
                continue
            for other_field, skip_list in skips[current].iteritems():
                if self.get_current(other_field) in skip_list:
                    return False
        return True
