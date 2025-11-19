
import sys


def run_replace_string():
    if len(sys.argv) < 2:
        print("Usage: python <text> <original char> <replace with>")
        sys.exit(1)
    text = sys.argv[1]

    chars_to_remove = str.maketrans("", "", "{}[]")
    result = text.translate(chars_to_remove)
    print(result)



run_replace_string()
