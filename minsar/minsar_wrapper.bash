#! /bin/bash
#set -x

MINSAR_LOG_DIR=~/minsar_log
mkdir -p $MINSAR_LOG_DIR

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    minsarApp.bash --help
    exit 0;
fi

PROJECT_NAME=$(basename "$1" | cut -d. -f1)

out_file="$MINSAR_LOG_DIR/$(date +"%Y%m%d:%H-%M")_$PROJECT_NAME"
cmd="(minsarApp.bash $@ | tee $out_file.o) 3>&1 1>&2 2>&3 | tee $out_file.e"
#cmd="(ls min* hello.log | tee $out_file.o) 3>&1 1>&2 2>&3 | tee $out_file.e"
echo "$cmd"
eval $cmd
    exit_status="$?"
    if [[ $exit_status -ne 0 ]]; then
       echo "minsarApp.bash exited with a non-zero exit code ($exit_status). Exiting."
       exit 1;
    fi
exit

