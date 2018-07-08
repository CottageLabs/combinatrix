# Combinatrix

Combinatrix is a utility library to produce a full set of variations of a set of parameters, according to a provided set of rules
for the values of those parameters, any inter-constraints/conditions on them.

It can take input in the form of a structured CSV or as a suitable JSON document.  It can also be integrated directly with your Python
code by providing a `dict` of with the appropriate configuration.

For example, if you are looking to generate an exhaustive set of paramters for parameterised testing, you can feed the sets of parameters
and their constraints into Combinatrix, and it will output all parameter sets that should be fed to your tests.


## Command Line

To use from the command line

* provide either a `-c` or a `-j` option, for an input CSV or JSON file respectively, containing the path to the source file
* provide an `-o` option if you want the resulting output to be written to a file, containing the path to the output file
* provide a `-p` option when using `-c` if you want the JSON obtained by converting the CSV written to file, containing the path to the output file
* privde a `-g` option when using `-c` if you want the combinations to be generated.  You can therefore omit this if you just want the CSV converted to JSON

for example

```
python combinatrix.py -c mycsv.csv -o combos.csv -p myjson.json -g yes
```

FIXME: when we're not on a plane, look up how to use argparse, to make -g and on/off switch.


## Options and Capabilities

### Field ordering

Fields are ordered in Combinatrix, primarily for the purposes of output display.  When you provide the fields for combination, you
provide them in order.  If you interact with the Combinatrix directly via the python API, and do not write your results out to CSV, they
you will be returned a `list` of `dict` objects which are not ordered.

For example, when provided with the following input

```json
{
    "parameters" : [
        {
            "name" : "field1"
        },
        {
            "name" : "field2"
        }
    ]
}
```

The resulting CSV output would be ordered the same way:

```
field1,field2
...,...
```


### Field Types

There are three field types, which behave in different ways during combnination:

#### Index

Fields of **index** type are not included in combinations.  Instead they result in a unique number (within the context of the combination set)
which defines an arbitrary order for the output.  The output will be provided in this order, whether it is the CSV output or the `list` of 
`dict` results from the python API.

For example, when provided with the following input:

```json
{
    "paramters" : [
        {
            "name" : "id",
            "type" : "index"
        },
        {
            "name" : "field1"
        }
    ]
}
```

The CSV output would be

```
id,field1
1,...
2,...
3,etc.
```

#### Generated

Fields of **generated** type are included in the combinations.  Each value for this type will be used in the combination, and its constraints
will be taken into account (see below for more information on constraints).  This is the default field type.  If a `type` parameter is omitted
from the settings, it will default to this.

For example, when provided with the following input:

```json
{
    "paramters" : [
        {
            "name" : "id",
            "type" : "index"
        },
        {
            "name" : "field1"
            "type" : "generated",
            "values" : {
                "one" : {},
                "two" : {}
            }
        }
    ]
}
```

Will result in the following CSV output

```
id,field1
1,one
2,two
```


### Conditional

Fields of type **conditional** will not be included in the combinations initially, but will have a suitable value attached to each
combination for which its supplied conditions (see below for more information) are satisfied.

This could be used, for example, to specify the expected output of a test, depending on the supplied arguments.  A conditional field
may also supply a `default` value, for use when none of its conditions apply.

For example, given the following input:

```json
{
    "paramters" : [
        {
            "name" : "id",
            "type" : "index"
        },
        {
            "name" : "field1"
            "type" : "generated",
            "values" : {
                "one" : {},
                "two" : {}
            }
        },
        {
            "name" : "result",
            "type" : "conditional",
            "default" : "success"
            "values" : {
                "error" : {
                    "conditions" : [
                        {"field1" : ["one"]}
                    ]
                }
            }
        }
    ]
}
```

The output CSV would be

```
id,field1,result
1,one,error
2,two,success
```


### Field Values

For **generated** and **conditional** types, you must specify the possible values.

For a **generated** type, this tells Combinatrix which values to use to build the full set of combinations.

For a **conditional** type, this tells Combinatrix which values are available, and can be used if their conditions are met.

For example, this document specifies a **generated** and a **conditional** field, which have the allowed values "one", "two" and "error"
respectively.  Note that the **conditional** field can also have a `default` value:

```json
{
    "paramters" : [
        {
            "name" : "field1"
            "type" : "generated",
            "values" : {
                "one" : {},
                "two" : {}
            }
        },
        {
            "name" : "result",
            "type" : "conditional",
            "default" : "success"
            "values" : {
                "error" : {}
            }
        }
    ]
}
```

Note also that each value is itself a key to a dictionary; within that dictionary we can place additional configuration for that value in
that field, see below.


### Combiation Constraints

Without any constraints, Combinatrix will generate a full set of combinations for all values in all **generated** fields.  So, for example,
the following document provides two unconstrained fields:

```json
{
    "paramters" : [
        {
            "name" : "field1"
            "type" : "generated",
            "values" : {
                "one" : {},
                "two" : {}
            }
        },
        {
            "name" : "field2",
            "type" : "generated",
            "values" : {
                "red" : {},
                "blue" : {},
                "green" : {}
            }
        }
    ]
}
```

The resulting CSV would be:

```
field1,field2
one,red
one,blue
one,green
two,red
two,blue
two,green
```

If you wanted to assert that "one" and "red" can never appear together in a combination, then this can be done by supplying a constraint:

In the configuration for the field, express that when field1 has the value "one", that "field2" must have the values "blue" or "green":

```json
{
    "name" : "field1"
    "type" : "generated",
    "values" : {
        "one" : {
            "contstraints" : {
                "field2" : ["blue", "green"]
            }
        },
        "two" : {}
    }
}
```

This would produce the following CSV, where the previous combination of "one" and "red" is no longer present:

```
field1,field2
one,blue
one,green
two,red
two,blue
two,green
```

This feature can be used to eliminate unnecessary or unwanted parameters from a set of test parameters, for example, where combinations
of certain parameters would make no sense.


### Conditions

You may wish to specify the value of certain fields depending on the values of other fields, independently of the combinations process.
This can be done with a **conditional** field, which specifies the value of the field against each combination after they have been
generated.

In the configuration for the field, for each value specify the `conditions` under which that value will be attached to a combination.

There can be multiple conditions for each value, each one specified as a separate object in the list of conditions.  Each condition may
refer to multiple fields in the combination, and each field may be specified with one or more possible values.

For example, to add the value "error" to a combination when both "field1" and "field2" have the value "none", you can specify the condition:

```json
{ 
    "field1" : ["none"], 
    "field2" : ["none"]
}
```

If you had other values that may cause an error, for example, if field1 contained the value "oops", this could be added thus:

```json
{ 
    "field1" : ["none", "oops"], 
    "field2" : ["none"]
}
```

The following example shows:

* ArgumentException if "field1" OR "field2" contain the value "none"
* AuthoriseException if "account" contains the value "unauthorised" or "unauthenticated"
* An empty string if none of the above conditions are met

```json
{
    "name" : "result",
    "type" : "conditional",
    "default" : "",
    "values" : {
        "ArgumentException" : {
            "conditions" : [
                { "field1" : ["none"] },
                { "field2" : ["none"] }
            ]
        },
        "AuthoriseException" : {
            "conditions" : [
                { "account" : ["unauthorised", "unauthenticated"] }
            ]
        }
    }
}
```

This feature is useful to specifying the outcomes of tests based on the input parameters.


## JSON/dict Format

The following example document from a real-world use case shows how arguments can be specified for the Combinatrix, either as a JSON file 
or as a python `dict`.

This document defines the parameters for a set of unit tests, which take the fields `application` and `account` with a variety of values
and inter-constraints, and which may raise certain kinds of exceptions conditional on the supplied parameters.

```json
{
	"parameters" : [
		{
			"name" : "test_id",
			"type" : "index"
		},
		{
			"name" : "application",
			"type" : "generated",
			"values" : {
				"none" : {
					"constraints" : {
						"application_status" : ["-"],
						"current_journal" : ["-"],
						"save" : ["success"]
					}
				},
				"exists" : {}
			}
		},
		{
			"name" : "account",
			"type" : "generated",
			"values" : {
				"none" : {},
				"publisher" : {},
				"admin" : {}
			}
		},
		{
			"name" : "save",
			"type" : "generated",
			"values" : {
				"success" : {},
				"fail" : {
					"constraints" : {
            			"application" : ["exists"]
					}
				}
			}
		},
		{
			"name" : "raises",
			"type" : "conditional",
			"default" : "",
			"values" : {
				"ArgumentException" : {
					"conditions" : [
						{ "application" : ["none"] },
						{ "account" : ["none"] }
					]
				},
				"AuthoriseException" : {
					"conditions" : [
						{
							"application" : ["exists"],
							"account" : ["unauthorised"]
						}
					]
				},
				"SaveException" : {
					"conditions" : [
						{ "save" : ["fail"] }
					]
				}
			}
		}
	]
}
```

## CSV Format

The CSV format is isomorphic with the JSON format, and allows you to manage your test parameters in a more convenient visual way.

The general format of the CSV is as follows:

* In the first column is a directive which tells us what kind of row follows
* The first row MUST be the field name
* All subsequent rows provide the appropriate setting for the field name in each column

The first row must therefore be something like

| field | test_id | field1 | field2 | condition1 | condition2 |
| ----- | ------- | ------ | ------ | ---------- | ---------- |

The first column tells us this is the `field` row, and then each subsequent column is the name of that field

We can then set the `type` of a field thus:

| field | test_id | field1 | field2 | condition1 | condition2 |
| ----- | ------- | ------ | ------ | ---------- | ---------- |
| type  | index   | generated | generated | conditional | conditional |

And the `default` value for columns where this is appropriate

| field | test_id | field1 | field2 | condition1 | condition2 |
| ----- | ------- | ------ | ------ | ---------- | ---------- |
| type  | index   | generated | generated | conditional | conditional |
| default |       |        |        | yes | no |

Note also that blank lines in the CSV are ignored, which can allow you to space the content for readability.

Further note that other than the first row, ordering of all subsequent rows is arbitrary.


### Defining Values

We can then optionally (though recommended for readability) set the values which will appear in each field.  If you do not specify
the values, then these will be inferred from the constraints and conditions (see below for more information).

The first column contains the text **value** then each subsequent cell in the row contains a value that the corresponding field
may take.  If the cell is empty, the value is ignored, which means you cannot set the empty string as an allowed value in your combination.

For example, suppose `field1` has two possible values, and `field2` has three possible values:

| field | test_id | field1 | field2 | condition1 | condition2 |
| ----- | ------- | ------ | ------ | ---------- | ---------- |
| type  | index   | generated | generated | conditional | conditional |
| default |       |        |        | yes | no |
|       |         |        |        |            |            |
| values |        | a      | 1      | yes        | yes        |
| values |        | b      | 2      | no         | no         |
| values |        |        | 3      |            |            |


### Defining Constraints

To add field constraints you provide a first column directive of the form **constraint [field name]**.  So to apply a constraint on 
values in `field` you would have the first column contain **constraint field1**: 

For example, the final row in the following table places a constraint on the value `a` in `field1` such that when `a` is the value in
a combination, then `field2` must have the value `1`:

For example:

| field | test_id | field1 | field2 | condition1 | condition2 |
| ----- | ------- | ------ | ------ | ---------- | ---------- |
| type  | index   | generated | generated | conditional | conditional |
| default |       |        |        | yes | no |
|       |         |        |        |            |            |
| values |        | a      | 1      | yes        | yes        |
| values |        | b      | 2      | no         | no         |
| values |        |        | 3      |            |            |
|       |         |        |        |            |            |
| constraint field1 | | a  | 1      |            |            |

You may provide the constraint in both directions, or leave it only in one direction.  For example, the following reflects the constraint
on `field1` for `field2` and also supplies an additional constraint on `field2` when its value is `3`:

| field | test_id | field1 | field2 | condition1 | condition2 |
| ----- | ------- | ------ | ------ | ---------- | ---------- |
| type  | index   | generated | generated | conditional | conditional |
| default |       |        |        | yes | no |
|       |         |        |        |            |            |
| values |        | a      | 1      | yes        | yes        |
| values |        | b      | 2      | no         | no         |
| values |        |        | 3      |            |            |
|       |         |        |        |            |            |
| constraint field1 | | a  | 1      |            |            |
| constraint field2 | | a  | 1      |            |            |
| constraint field2 | | b  | 3      |            |            |

In this simple example, the constraints for `field1` and `field2` are equivalent, but the need to be able to specify which field 
constrains which other fields is more obvious when there are 3 or more fields, and multiple co-dependent constraints.


### Defining Conditionals

To add conditionals, you provide a first column directive of the form **conditional [field name]**.  So to apply a conditional value
for `condition1`, you would have the first column contain **conditional condition1**. 

For example, the final row in the following table adds a condition such that `condition1` is `yes` whenever `field1` is `b`:

| field | test_id | field1 | field2 | condition1 | condition2 |
| ----- | ------- | ------ | ------ | ---------- | ---------- |
| type  | index   | generated | generated | conditional | conditional |
| default |       |        |        | yes | no |
|       |         |        |        |            |            |
| values |        | a      | 1      | yes        | yes        |
| values |        | b      | 2      | no         | no         |
| values |        |        | 3      |            |            |
|       |         |        |        |            |            |
| constraint field1 | | a  | 1      |            |            |
| constraint field2 | | a  | 1      |            |            |
| constraint field2 | | b  | 3      |            |            |
|       |         |        |        |            |            |
| conditional condition1 | | a |    | yes        |            |


### Lists of OR values

TODO

### Lists of NOR values

TODO

## Test Integration

Combinatrix is designed to allow you to plug combinations directly into parameterised tests, and it does this through the concept of a
test "bundle".

Each bundle consists of one or both of a settings CSV and settings JSON, and the resulting test matrix itself.

To execute a test based on a test bundle, we can use [parameterized](https://github.com/wolever/parameterized) as follows:


```python
import unittest
from parameterized import parameterized
from combinatrix.testintegration import load_parameter_sets, rel2abs

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "resources", "bundles", "combine"), "combine", "test_id", {"test_id" : []})

class TestCombine(unittest.TestCase):

    @parameterized.expand(load_cases)
    def test_combine(self, name, kwargs):
        pass
```

Here we have defined a test class called `TestCombine` which extends the `unittest.TestCase`.  In turn this contains a single test function
called `test_combine` which takes two arguments:

* name - the name of the test
* kwargs - a dictionary of arguments for the test

This function is annotated with `@parameterized.expand(load_cases)`.  This is a feature of *parameterized* which will load the test cases
from the supplied function, and inject them into the test class at run-time.

We therefore have also defined a function called `load_cases` which uses Combinatrix to deliver the test cases.


### Loading Parameter Sets

There is a function provided which can load parameter sets and pass them to *parameterized*:

```python
from combinatrix.testintegration import load_parameter_sets, rel2abs

def load_cases():
    return load_parameter_sets(rel2abs(__file__, "..", "resources", "bundles", "combine"), "combine", "test_id")
```

`load_parameter_sets` is invoked with the following arguments:

* The path to the test "bundle" for this test
* The name of the test "bundle"
* The field in the test matrix which will define the name of the test
* An optional filter which will allow us to limit the parameter sets to a subset of the total

Note also we provide a convenience function `rel2abs` which allows us to convert relative paths to absolue paths easily.

The above example loads a bundle called **combine** from the directory **../resources/bundles/combine**.  It tells us that the field
**test_id** is the field that will uniquely name each test, and it applies a filter


## Advanced Topics

### Conflict Detection

TODO