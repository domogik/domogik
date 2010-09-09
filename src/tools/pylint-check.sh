#!/bin/bash

# TODO : set config file and use it
CONFIG_FILE=
OUTPUT_GOOD_FILES=/tmp/pylint-ok.csv
OUTPUT_BAD_FILES=/tmp/pylint-ko.csv

SEUIL=8,00

# Empty output files
> $OUTPUT_GOOD_FILES
if [ $? -ne 0 ] ; then
    echo "Error on creating $OUTPUT_GOOD_FILES"
    exit 1
fi
> $OUTPUT_BAD_FILES
if [ $? -ne 0 ] ; then
    echo "Error on creating $OUTPUT_BAD_FILES"
    exit 1
fi

# Check all files with pylint
for fic in $(find . -name "*.py")
  do
    echo "==== $fic ===="
    RESULT=$(pylint $fic | grep "Your code has been rated")
    NOTE=$(echo $RESULT | sed "s/Your code.*at //" | sed "s/(previous.*$//" | cut -d"/" -f1 -s | sed "s/\./,/")
    echo "Note : $NOTE/10"
    if [[ $NOTE > $SEUIL || $NOTE == "10,00" ]] ; then
        echo "$fic;$NOTE;OK" >> $OUTPUT_GOOD_FILES
    else
        echo "$fic;$NOTE;KO" >> $OUTPUT_BAD_FILES
    fi
done

# Display result
echo "Good files :"
cat $OUTPUT_GOOD_FILES | sort
echo "Bad files :"
cat $OUTPUT_BAD_FILES | sort
