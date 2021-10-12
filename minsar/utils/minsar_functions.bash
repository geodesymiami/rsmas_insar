#! /bin/bash
function get_reference_date(){ 
   reference_date=( $(xmllint --xpath 'string(/productmanager_name/component[@name="instance"]/component[@name="bursts"]/component[@name="burst1"]/property[@name="burststartutc"]/value)' \
                    reference/IW*.xml | cut -d ' ' -f 1 | sed "s|-||g") )
   echo $reference_date
}

#####################################################################
function countbursts(){ files=()
                   subswaths=reference/???
                   unset array
                   declare -a array 
                   for subswath in $subswaths; do
                       last=`ls $subswath/burst*xml | tail -1`
                       array+=($(basename $last))
                   done;
                   reference_date=$(get_reference_date)
                   echo "reference/$reference_date  #of_bursts: `ls reference/IW*/burst*xml | wc -l`   ${array[@]}"

                   dates="secondarys/*"
                   for date in $dates; do
                       subswaths=$date/???
                       unset array
                       declare -a array 
                       for subswath in $subswaths; do
                           last=`ls $subswath/burst*xml | tail -1`
                           array+=($(basename $last))
                       done;
                       echo "$date #of_bursts: `ls $date/IW*/burst*xml | wc -l`   ${array[@]}"
                   done;
                   }
