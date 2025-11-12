import sys


def convert(path):
    x = path.replace("\\", "/")
    print(x)
    return x

if len(sys.argv) < 2:
    print("Error: No path provided. Usage: python convert_win_2_unix.py <path>", file=sys.stderr)
    sys.exit(1)

path = sys.argv[1]
convert(path)