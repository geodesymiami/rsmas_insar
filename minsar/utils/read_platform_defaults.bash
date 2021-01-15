#!/bin/bash

job_defaults_file="${HOME}/accounts/suggestion_platforms_defaults.cfg"
platform_name=$(echo $PLATFORM_NAME | tr '[:upper:]' '[:lower:]')

export_vars=$(grep "PLATFORM_NAME" $job_defaults_file | grep -vx '#.*')
values=$(grep "${platform_name}" $job_defaults_file | grep -vx '#.*')

export_vars=($export_vars)
values=($values)

length=$((${#export_vars[@]}-1))
for i in $(seq 1 $length); do
    var="${export_vars[$i]}"
    val="${values[$i]}"

    varname=$(eval "echo \$${var}")
        
    if [[ ! -z "$varname" ]]; then
	eval "echo '$var' already set to \'\$${var}\'"
     	continue;
    fi
    eval "export $var=$val"
    echo "$var=$val"
done
