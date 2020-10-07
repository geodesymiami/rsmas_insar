#! /bin/bash
#set -x

get_num_projects (){
    jobs=($(squeue -u $USER | grep -oP "[0-9]{7,}"))

    projects=()
    for j in ${jobs[@]}; do
	    workdir=$(scontrol show jobid -dd $j | grep WorkDir)
	    IFS="/"
	    project=($workdir)
	    project=${project[-1]}
	    projects+=($project)
	    unset IFS
    done

    unique_projects=($(echo "${projects[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))
    num_projects=${#unique_projects[@]}
    return $num_projects
}

MINSAR_LOG_DIR=~/minsar_log
mkdir -p $MINSAR_LOG_DIR

if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    minsarApp.bash --help
    exit 0;
fi

PROJECT_NAME=$(basename "$1" | cut -d. -f1)

num_projects=$(get_num_projects)

while [ $num_projects -gt 4 ]; do
    echo "Max number of running projects reached. Waiting 5 minutes to try again."
    sleep 300
    num_projects=$(get_num_projects)
done

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

