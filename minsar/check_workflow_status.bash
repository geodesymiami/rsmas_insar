##!/bin/bash

function get_active_jobids {
    running_tasks=$(squeue -u $USER --format="%A" -rh)
    job_ids=($(echo $running_tasks | grep -oP "\d{4,}"))
    echo "${job_ids[@]}"
    return 0
}

function contains_element {
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}

jobnumbers=($(get_active_jobids))
active_workflows=()

for jn in "${jobnumbers[@]}"; do
    wflow=$(echo "$(scontrol show jobid -dd $jn)" | grep -oP "(?<= WorkDir=)(.*)")
    contains=$(contains_element "$wflow" "${active_workflows[@]}")
    contains="$?"
    if [[ $contains -ne 0 ]]; then
        active_workflows+=("$wflow")
    fi
done

for wf in "${active_workflows[@]}"; do
    cd $wf
    project_name=$(basename $wf)
    num_logfiles=$(ls submit_jobs.*.log | wc -l)
    num_logfiles=$(($num_logfiles-1))
    last_tableline=$(tail -200 submit_jobs.${num_logfiles}.log | grep -P "^\|\s(run_\d{2}|small|insar)" | tail -1)
    step_partial=$(echo $last_tableline | grep -oP "run_\d{2}|small|insar")
    step_name=$(basename $(ls run_files/$step_partial*.job | tail -1) | grep -oP "(.*)(?=_\d{1,}.job)")

    grep -P "^\|\s$step_partial" "submit_jobs.${num_logfiles}.log" > temp.txt
    jobnumbers=($(grep -oP "\d{7,}" temp.txt))
    num_jobnumbers=$(echo "${#jobnumbers[@]}")

    total=$(ls run_files/$step_partial*.job | wc -l)
    num_unsubmitted=$(($total-$num_jobnumbers))

    start_time=$(grep -oP "(?<=Started at: )(.*)" submit_jobs.${num_logfiles}.log)
    dt=$(date -d"$start_time" "+%s")

    num_complete=0
    num_running=0
    num_pending=0
    num_other=0
    for jn in "${jobnumbers[@]}"; do
        state=$(sacct --format="State" -j $jn | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' | head -3 | tail -1 )

        if [[ $state == *"COMPLETED"* ]]; then
            num_complete=$(($num_complete+1))
        elif [[ $state == *"RUNNING"* ]]; then
            num_running=$(($num_running+1))
        elif [[ $state == *"PENDING"* ]]; then
            num_pending=$(($num_pending+1))
        else
            num_other=$(($num_other+1))
        fi
    done
    end=$(date +%s)
    elapsed=$(($end-$dt))

    hours=$(printf "%02d" $(($elapsed/3600)))
    mins=$(printf "%02d" $(($elapsed%3600/60)))
    seconds=$(printf "%02d" $(($elapsed%3600%60)))

    echo -e "$project_name $step_name: $num_complete COMPLETED, $num_running RUNNING, $num_pending PENDING, $num_unsubmitted UNSUBMITTED, $num_other OTHER \t | ${hours}:${mins}:${seconds} elapsed."
done