import sys


def convert():
    x = path.replace("\\", "/")
    print(x)
    return x


path = sys.argv[1]
convert()
