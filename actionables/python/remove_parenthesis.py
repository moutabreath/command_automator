
import sys


def run_replace_string():
    if len(sys.argv) != 2:
        print("Usage: python <text> <original char> <replace with>")
        sys.exit(1)
    text = sys.argv[1]
    # source_to_replace = sys.argv[2]
    # replace_to = sys.argv[3]

    x = text.replace("{", "")
    x = x.replace("}", "")
    print(x)



run_replace_string()
