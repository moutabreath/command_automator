#!/bin/bash
# Convert unix path to win path - works
line=$(sed -e 's#^J:##' -e 's#/#\\#g' <<< "$1")
echo $line

path=$1
path=$path  | perl -pe 's/\\/\\\\/g'


python ../utils/convertWin2Unix.py "$path"# echo $path