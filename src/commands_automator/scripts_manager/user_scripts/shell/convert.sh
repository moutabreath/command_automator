#!/bin/bash
# Convert unix path to win path - works
line=$(sed -e 's#^J:##' -e 's#/#\\#g' <<< "$1")
echo $line

path=$(perl -pe 's/\\/\\\\/g' <<< "$1")

python ../utils/convertWin2Unix.py "$path"