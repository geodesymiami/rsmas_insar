#! /bin/bash
###########################################
function changequeuenormal() { 
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
   echo "  Usage: changequeuenormal run_10*.job"; return
fi
if [[ $PLATFORM_NAME == "frontera" ]] ; then
          sed -i "s|flex|normal|g" "$@" ;
          sed -i "s|small|normal|g" "$@" ;
          sed -i "s|development|normal|g" "$@" ;
elif [[ $PLATFORM_NAME == "stampede2" ]] ; then 
          sed -i "s|skx-dev|skx-normal|g" "$@" ;
fi 
}

###########################################
function changequeuedev() { 
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
   echo "  Usage: changequeuedev run_10*.job"; return
fi
if [[ $PLATFORM_NAME == "frontera" ]] ; then
          sed -i "s|flex|development|g" "$@" ;
          sed -i "s|small|development|g" "$@" ;
          sed -i "s|normal|development|g" "$@" ;
elif [[ $PLATFORM_NAME == "stampede2" ]] ; then 
          sed -i "s|skx-normal|skx-dev|g" "$@" ;
fi 
}

###########################################
function changequeueflex() { 
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
   echo "  Usage: changequeueflex run_10*.job"; return
fi
if [[ $PLATFORM_NAME == "frontera" ]] ; then
          sed -i "s|normal|flex|g" "$@" ;
          sed -i "s|small|flex|g" "$@" ;
          sed -i "s|development|flex|g" "$@" ;
fi 
}

#function changequeuedev() { sed -i "s|skx-normal|$QUEUE_DEV|g"  "$@" ; sed -i "s|flex|$QUEUE_DEV|g"  "$@" ; sed -i "s|normal|$QUEUE_DEV|g"  "$@" ; }
#function changequeuesmall() { sed -i "s|flex|small|g" "$@" ; sed -i "s|development|small|g" "$@" ; }
#function changequeueflex()  { sed -i "s|small|flex|g" "$@" ; sed -i "s|development|flex|g"  "$@" ; }

#####################################################################
function get_reference_date(){ 
   reference_date=( $(xmllint --xpath 'string(/productmanager_name/component[@name="instance"]/component[@name="bursts"]/component[@name="burst1"]/property[@name="burststartutc"]/value)' \
                    reference/IW*.xml | cut -d ' ' -f 1 | sed "s|-||g") )
   echo $reference_date
}

#####################################################################
function countbursts(){ 
                   #set -xv
                   subswaths=geom_reference/*
                   unset array
                   declare -a array 
                   for subswath in $subswaths; do
                       icount=`ls $subswath/hgt*rdr | wc -l`
                       array+=($(basename $icount))
                   done;
                   reference_date=$(get_reference_date)
                   echo "geom_reference/$reference_date   #of_bursts: `ls geom_reference/IW*/hgt*rdr | wc -l`   ${array[@]}"

                   dates="coreg_secondarys/*"
                   for date in $dates; do
                       subswaths=$date/???
                       unset array
                       declare -a array 
                       for subswath in $subswaths; do
                           icount=`ls $subswath/burst*xml | wc -l`
                           array+=($(basename $icount))
                       done;
                       echo "$date #of_bursts: `ls $date/IW*/burst*xml | wc -l`   ${array[@]}"
                   done;
                   }
###########################################
function check_matplotlib_pyplot(){ 
   #set -x
   timeout 20 python -c "import matplotlib.pyplot"
   exit_status=$?
   if [[ $exit_status -ne 0 ]]; then
      echo "Can't import. Reason unknown. Try a new shell (exit_status: $exit_status)"
      return 1;
   fi
   #echo Continue ... python -c \"import matplotlib.pyplot\" was successful within 6 secs
   echo "        ... successful, continue ... "
   return 0
}

