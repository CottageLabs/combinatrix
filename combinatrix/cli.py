import argparse
from combinatrix.core import convert_csv, fromcsv, fromjsonfile


def main():
    parser = argparse.ArgumentParser(prog="combinatrix",
                                     description="Conbinatrix: Produce a full set of variations of a set of parameters, according to a provided set of rules \
                                                    for the values of those parameters, any inter-constraints/conditions on them.")

    parser.add_argument("input", help="Source input file; can be either CSV or JSON, and should end with either .csv or .json")
    parser.add_argument("-c", "--csv", action="store_true", help="if the input file does not end with .csv but is a CSV, use this flag to force that format")
    parser.add_argument("-j", "--json", action="store_true", help="if the input file does not end with .csv but is a CSV, use this flag to force that format")
    parser.add_argument("-m", "--matrix", help="output file path for matrix.  If omitted, the matrix will not be generated")
    parser.add_argument("-s", "--settings", help="output file path for JSON settings, if this is a conversion from a CSV settings file")

    args = parser.parse_args()

    if not args.input:
        print("You must specify an input file")
        parser.print_help()
        exit()

    if args.csv and args.json:
        print("Specify either -c/--csv or -j/--json, or neither, but not both")
        parser.print_help()
        exit()

    is_csv = args.csv
    is_json = args.json
    if not is_csv and not is_json:
        is_csv = args.input.endswith(".csv")
        is_json = args.input.endswith(".json")

    if not is_csv and not is_json:
        print("Unable to determine the format of the input.  Please ensure you have a file which ends with .csv or .json, or force the format via -c/-j")
        parser.print_help()
        exit()

    if not args.matrix and not args.settings:
        print("You must specify at least one output file with -m and/or -s")
        parser.print_help()
        exit()

    # if we've been given a csv, and the path to output the settings, but not a path to output the matrix, then just
    # covert the csv
    if is_csv and args.settings and not args.matrix:
        convert_csv(args.input, args.settings)

    # if we've been given a csv, and the path to the output matrix, then do a full conversion to csv.  If we've also
    # been provided with a path to the settings, these will get written, otherwise they won't
    elif is_csv and args.matrix:
        fromcsv(args.input, args.matrix, args.settings)

    # if we've been given json, and the path to the output matrix, then do a conversion to the matrix.
    elif is_json and args.matrix:
        fromjsonfile(input, args.matrix)

    else:
        print("Unable to find a suitable path to execute")
        parser.print_help()
        exit()


if __name__ == "__main__":
    main()
