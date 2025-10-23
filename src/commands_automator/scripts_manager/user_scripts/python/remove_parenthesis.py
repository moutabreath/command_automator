
import sys


def run_replace_string():
    if len(sys.argv) < 2:
        print("Usage: python <text> <original char> <replace with>")
        sys.exit(1)
    text = sys.argv[1]

    x = text.replace("{", "")
    x = x.replace("}", "")
    x = x.replace("[", "")
    x = x.replace("]", "")
    x = x.replace("(", "")
    x = x.replace(")", "")   
    print(x)



run_replace_string()
