#!/usr/bin/env bash
###########################################
function changequeuenormal() { 
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
   echo "  Usage: changequeuenormal run_10*.job"; return
fi
if [[ $PLATFORM_NAME == "frontera" ]] ; then
          sed -i "s|flex|normal|g" "$@" ;
          sed -i "s|small|normal|g" "$@" ;
          sed -i "s|development|normal|g" "$@" ;
elif [[ $PLATFORM_NAME == "stampede3" ]] ; then 
          sed -i "s|dev|skx|g" "$@" ;
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
elif [[ $PLATFORM_NAME == "stampede3" ]] ; then 
          sed -i "s|skx|dev|g" "$@" ;
fi 
sed -i "s|SBATCH -t .:..:|SBATCH -t 1:59:|g" "$@" ; 
sed -i "s|SBATCH -t ..:..:|SBATCH -t 01:59:|g" "$@" ;
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
function changequeuesmall() { sed -i "s|flex|small|g" "$@" ; sed -i "s|development|small|g" "$@" ; sed -i "s|normal|small|g" "$@" ; }
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
   timeout 120 python -c "import matplotlib.pyplot"
   exit_status=$?
   if [[ $exit_status -ne 0 ]]; then
      echo "Can't import. Reason unknown. Try a new shell (exit_status: $exit_status)"
      return 1;
   fi
   #echo Continue ... python -c \"import matplotlib.pyplot\" was successful within 6 secs
   echo "        ... successful, continue ... "
   return 0
}
###########################################
function listc() { 
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                       \n\
  Examples:                                      \n\
      listc ChamanChunk24SenAT144                \n\
      listc ChamanBigSenAT144                    \n\
      listc ChamanChunksSenAT144                 \n\
      listc SenAT144                             \n\
      listc C*SenAT144                           \n\
                                                 \n\
  List progress of chunk-wise processing.        \n\n\
  Lists S1* files (if exist) or out_* files. Unnecessary string  \n\
  (e.g. Chunk24, Big, Chunks) are stripped from argument. \n\
  Run in \$SCRATCHDIR.  \n
    "
    printf "$helptext"
    return
fi

not_finished=()
arg=$1
arg_mod=*$arg
# modify argument if it contains Chunk or Big
[[ $arg == *"Chunk"* ]] && arg_mod=$(echo $arg | sed -e s/Chunk.\*Sen/\*Sen/)
[[ $arg == *"Big"* ]] && arg_mod=$(echo $arg | sed -e s/Big.\*Sen/\*Sen/)
[[ $arg == *"Chunks"* ]] && arg_mod=$(echo $arg | sed -e s/Chunks.\*Sen/\*Sen/)
#echo Original_argument: $arg 
#echo Modified_argument: ${arg_mod} 

dir_list=$(ls -d $arg_mod)
for dir in $dir_list; do
   S1_files=( $dir/mintpy/S1* )
   if [[  ${#S1_files[@]} -ne 1 ]]; then
      echo "Too many S1* files: ${S1_files[@]}"
      return
   fi

   if  test -f $dir/mintpy/S1*  ; then
      ls -lh $dir/mintpy/S1* | awk  '{printf "%5s %s %2s %s %s\n", $5,$6,$7,$8,$9}'
   else
      not_finished+=($dir)
   fi
done; 
for dir in ${not_finished[@]}; do
    if [[ $dir != *Big* ]] && [[ $dir != *ChunksS* ]]; then
       #ls -lvd $dir/{,out_run*.e}  | awk  '{print $5,$6,$7,$8,$9}'
       ls -lvd $dir/{,out_run*.e}  | awk  '{printf "%5s %s %2s %s %s\n", $5,$6,$7,$8,$9}'
    fi
done
}

###########################################
function add_ref_lalo_to_file() { 
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="                                       \n\
  Examples:                                      \n\
      add_ref_lalo_to_file  S1_IW1_128_0596_0597_20160605_XXXXXXXX_S00860_S00810_W091190_W091130_Del4PS.he5                \n\
                                                 \n\
  adds REF_LAT, REF_LON to file (read from geo_velocity.h5)  \n
    "
    printf "$helptext"
    return
fi

file=$1

echo adding to $file
REF_LAT=$(info.py geo/geo_velocity.h5 | grep REF_LAT | awk '{print $2}')
REF_LON=$(info.py geo/geo_velocity.h5 | grep REF_LON | awk '{print $2}')

$MINTPY_HOME/src/mintpy/legacy/add_attribute.py $file REF_LAT=${REF_LAT}
$MINTPY_HOME/src/mintpy/legacy/add_attribute.py $file REF_LON=${REF_LON}
}

###########################################
function rsyncFJ() { 
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="            \n\
  rsyncFJ:  rsync directory From Jetstream (FJ) server to local \$SCRATCHDIR \n\
                            requires local \$SCRATCHDIR environment variable\n\
                                                 \n\
  Examples:                                      \n\
     rsyncFJ MaunLoaSenAT124                     \n\
     rsyncFJ MaunLoaSenAT124/mintpy_5_20         \n\
     rsyncFJ unittestGalapagosSenDT128/miaplpy/network_single_reference \n\
"
    printf "$helptext"
    return
fi

if [[ $# -eq 0 && $(basename $(dirname $PWD)) == "scratch" ]]; then
  dir=$(basename $PWD)
else
  dir=$1
fi

set -v
echo "test:"
if [ ! -d "$SCRATCHDIR/$dir" ]; then
  echo "dir $SCRATCHDIR/$dir does not exist, making it"
  mkdir -p $SCRATCHDIR/$dir
fi

echo "Syncing directory $dir from jetstream:"
cmd="rsync -avzh exouser@149.165.154.65:/data/HDF5EOS/$dir/ $SCRATCHDIR/$dir"
echo running ... $cmd
$cmd

if [[ $dir == *"network"* ]]; then
  cmd="rsync -avzh exouser@149.165.154.65:/data/HDF5EOS/${dir%/*}/maskPS.h5 $SCRATCHDIR/${dir%/*}/maskPS.h5"
  echo running ... $cmd
  $cmd
  cmd="rsync -avzh exouser@149.165.154.65:/data/HDF5EOS/$dir/inputs/geometryRadar.h5 $SCRATCHDIR/$dir/inputs"
  echo running ... $cmd
  $cmd
fi

}

###########################################
function rsyncTJ() { 
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
helptext="            \n\
  rsyncTJ:  rsync directory TO JETSTREAM server from local $SCRATCHDIR \n\
                                                 \n\
  Examples:                                      \n\
            (from $SCRATCHDIR:)                  \n\
     rsyncTJ MaunLoaSenAT124                     \n\
                                                 \n\
            (from /scratch/MaunaLoaSenAT124:)     \n\
     rsyncTJ                                     \n\
    "
    printf "$helptext"
    return
fi

if [[ $# -eq 0 && $(basename $(dirname $PWD)) == "scratch" ]]; then
  dir=$(basename $PWD)
else
  dir=$1
fi

echo "Syncing directory $dir from jetstream:"
cmd="rsync -avzh $SCRATCHDIR/$dir/ exouser@149.165.154.65:/data/HDF5EOS/$dir "
echo running ... $cmd
$cmd
}

