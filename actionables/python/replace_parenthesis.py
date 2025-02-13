
import sys


def run_replace_string():
    if len(sys.argv) <= 3:
        print("Usage: python <text>  <original char> <replace with> <original char> <replace with> ...")
        sys.exit(1)
    text = sys.argv[1]    

    for i in range(2, len(sys.argv) - 1, 2):
        source_to_replace = sys.argv[i]
        replace_to = sys.argv[i + 1]        
        text = text.replace(source_to_replace, replace_to)
    print(text)

run_replace_string()
