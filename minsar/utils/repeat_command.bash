#!/usr/bin/env bash


# Check for help option
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "                               "
    echo "Usage: $(basename $0) <command>"
    echo "       This script repeats <command> every 60 seconds for a total time of 6 hours if a failure occurs."
    echo "                               "
    exit 0
fi

# Command to be executed, taken from command line arguments
COMMAND="$@"

# Total duration for attempts is 6 hours = 360 minutes
# Interval between attempts is 60 seconds
TOTAL_DURATION=360
INTERVAL=60

# Calculate the number of attempts
let ATTEMPTS=TOTAL_DURATION*60/INTERVAL

echo "Attempting to execute command every $INTERVAL seconds for $TOTAL_DURATION minutes..."

for (( i=1; i<=ATTEMPTS; i++ ))
do
    echo "Attempt $i of $ATTEMPTS"
    
    # Execute the command
    eval $COMMAND
    
    # Check if the command succeeded
    if [ $? -eq 0 ]; then
        echo "Command succeeded."
        exit 0
    else
        echo "Command failed. Waiting $INTERVAL seconds before retrying..."
        sleep $INTERVAL
    fi
done
