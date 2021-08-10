#!/bin/bash
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                             \n\
  usage: read_cfg.bash file.cfg                        \n\
                                                       \n\
  Examples:                                            \n\
     read_cfg.bash ~/accounts/platform_defaults.cfg    \n\
                                                       \n\
     "
    printf "$helptext"
    exit 0;
else
   defaults_file="${HOME}/accounts/platforms_defaults.cfg"
   platform_name=$(echo $PLATFORM_NAME | tr '[:upper:]' '[:lower:]')
   
fi

echo $platform_name

exit

export_vars=$(grep "PLATFORM_NAME" $defaults_file | grep -vx '#.*')
values=$(grep "${platform_name}" $defaults_file | grep -vx '#.*')

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
