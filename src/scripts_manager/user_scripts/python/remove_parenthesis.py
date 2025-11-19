
import sys


def run_replace_string():
    if len(sys.argv) < 2:
        print("Usage: python remove_parenthesis.py <text>")
        sys.exit(1)    
    text = sys.argv[1]
    chars_to_remove = str.maketrans("", "", "{}[]")
    result = text.translate(chars_to_remove)
    print(result)


if __name__ == "__main__":
    run_replace_string()
