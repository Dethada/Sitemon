#!/bin/bash

KEEP='NO'
# bash generate random 10 character alphanumeric string (upper and lowercase) 
OUTPUT=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 10 | head -n 1).jpg

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -u|--url)
    URL="$2"
    shift # past argument
    shift # past value
    ;;
    -o|--output)
    OUTPUT="$2"
    shift # past argument
    shift # past value
    ;;
    -k|--keep)
    KEEP="YES"
    shift # past argument
    ;;
    -h|--help)
    HELP="YES"
    shift # past argument
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

if [[ "$HELP" == "YES" ]]
then
    echo -ne '-u/--url for url\n-o/--output for output filename\n-k/--keep to keep the image file\n'
    exit 0
fi

if [ -z "$URL" ] || [ -z "$OUTPUT" ]
then
    echo -ne "Missing arguments -h/--help for help\n"
    exit 1
fi

./screenshot.js -u $URL -o $OUTPUT && ./ihash.py -f $OUTPUT

if [[ "$KEEP" == "NO" ]]
then
    [ -e $OUTPUT ] && rm -f $OUTPUT
fi