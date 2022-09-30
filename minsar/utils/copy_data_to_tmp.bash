##! /bin/bash
#trap "set +x; sleep 1; set -x" DEBUG

function distribute_secondarys {
    batch_file="$1"
    out_dir="$2"

    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n",$NF}' ) )
    mkdir -p /tmp/secondarys
    for date in "${date_list[@]}"; do
        distribute.bash $out_dir/secondarys/$date /tmp/secondarys; 
        mv /tmp/$date /tmp/secondarys
    done
    files1="/tmp/secondarys/????????/*.xml"
    files2="/tmp/secondarys/????????/*/*.xml"
    old=$out_dir 
    sed -i "s|$old|/tmp|g" $files1
    sed -i "s|$old|/tmp|g" $files2
}

function distribute_reference {
    out_dir="$1"
    distribute.bash $out_dir/reference
    files="/tmp/reference/*.xml /tmp/reference/*/*.xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files
}

job_name="$1"
batch_file="$2"
out_dir="$3"
if [[ $4 ]]; then
    distribute_file="$4"
fi

module load TACC
# ------------------

if [[ $job_name != *"unpack_topo_reference"* && $job_name != *"unpack_secondary_slc"* ]]; then
    
    if [[ $PLATFORM_NAME == *"stampede2"* ]]; then
        export CDTOOL=/scratch/01255/siliu/collect_distribute
    elif [[ $PLATFORM_NAME == *"frontera"* ]]; then
        export CDTOOL=/scratch1/01255/siliu/collect_distribute
    fi
    module load intel/19.1.1 2> /dev/null
    export PATH=${PATH}:${CDTOOL}/bin
fi

if [[ $job_name == *"run_02_unpack_secondary_slc"* ]]; then

    module load ooops
    # dummy-to-pop

elif [[ $job_name == *"average_baseline"* ]]; then

    #cp -r $out_dir/reference /tmp
    distribute_reference $out_dir
    # secondarys
    distribute_secondarys $batch_file $out_dir

elif [[ $job_name == *"fullBurst_geo2rdr"* ]]; then

    distribute_reference $out_dir

    # geom_reference
    distribute.bash $out_dir/geom_reference 
    files="/tmp/geom_reference/*/*.xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files

    # secondarys
    distribute_secondarys $batch_file $out_dir

elif [[ $job_name == *"fullBurst_resample"* ]]; then

    distribute_reference $out_dir

    # secondarys
    distribute_secondarys $batch_file $out_dir

elif [[ $job_name == *"merge_reference_secondary_slc"* ]]; then

    distribute.bash $out_dir/stack
    files="/tmp/stack/*xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files

    # reference
    distribute_reference $out_dir

    # coreg_secondarys      (different awk)
    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n",$NF}' | sed -n '/^[0-9]/p' ) )
    ref_date=( $(xmllint --xpath 'string(/productmanager_name/component[@name="instance"]/component[@name="bursts"]/component[@name="burst1"]/property[@name="burststartutc"]/value)' $out_dir/reference/IW*.xml | cut -d ' ' -f 1 | sed "s|-||g") )

    # remove ref_date from array
    index=$(echo ${date_list[@]/$ref_date//} | cut -d/ -f1 | wc -w | tr -d ' ')
    unset date_list[$index]
    if [[ ${#date_list[@]} -ne 0 ]]; then
        mkdir -p /tmp/coreg_secondarys
        for date in "${date_list[@]}"; do
            distribute.bash $out_dir/coreg_secondarys/$date; mv /tmp/$date /tmp/coreg_secondarys
        done
        files1="/tmp/coreg_secondarys/????????/*.xml"
        files2="/tmp/coreg_secondarys/????????/*/*.xml"
        old=$out_dir
        sed -i "s|$old|/tmp|g" $files1
        sed -i "s|$old|/tmp|g" $files2
    fi

elif [[ $job_name == *"generate_burst_igram"* ]]; then

    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n%s\n",$(NF-1),$NF}' | sort -n | uniq ) )
    ref_date=( $(xmllint --xpath 'string(/productmanager_name/component[@name="instance"]/component[@name="bursts"]/component[@name="burst1"]/property[@name="burststartutc"]/value)' $out_dir/reference/IW*.xml | cut -d ' ' -f 1 | sed "s|-||g") )
    
    # reference
    if [[ " ${date_list[@]} " =~ " $ref_date " ]] ; then
        distribute_reference $out_dir
    fi
    
    # remove ref_date from array
    index=$(echo ${date_list[@]/$ref_date//} | cut -d/ -f1 | wc -w | tr -d ' ')
    unset date_list[$index]
    if [[ ${#date_list[@]} -ne 0 ]]; then
        mkdir -p /tmp/coreg_secondarys
        for date in "${date_list[@]}"; do
            distribute.bash $out_dir/coreg_secondarys/$date; mv /tmp/$date /tmp/coreg_secondarys
        done
        files1="/tmp/coreg_secondarys/????????/*.xml"
        files2="/tmp/coreg_secondarys/????????/*/*.xml"
        old=$out_dir
        sed -i "s|$old|/tmp|g" $files1
        sed -i "s|$old|/tmp|g" $files2
    fi

elif [[ $job_name == *"merge_burst_igram"* ]]; then

    distribute.bash $out_dir/stack
    files="/tmp/stack/*xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files

    # interferograms
    pair_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _merge_igram_ '{printf "%s\n",$2}' | sort -n | uniq) )
    mkdir -p /tmp/interferograms
    for pair in "${pair_list[@]}"; do
        distribute.bash $out_dir/interferograms/$pair; mv /tmp/$pair /tmp/interferograms
    done
    files1="/tmp/interferograms/????????_????????/*.xml"
    files2="/tmp/interferograms/????????_????????/*/*.xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files1
    sed -i "s|$old|/tmp|g" $files2

elif [[ $job_name == *"filter_coherence"* ]]; then

    # merged/interferograms       
    pair_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _igram_filt_coh_ '{printf "%s\n",$2}' | sort -n | uniq) )
    mkdir -p /tmp/merged/interferograms
    for pair in "${pair_list[@]}"; do
        distribute.bash $out_dir/merged/interferograms/$pair; mv /tmp/$pair /tmp/merged/interferograms
    done
    files1="/tmp/merged/interferograms/????????_????????/*.xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files1

    # merged/SLC
    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n%s\n",$(NF-1),$NF}' | sort -n | uniq) )
    mkdir -p /tmp/merged/SLC
    for date in "${date_list[@]}"; do
        distribute.bash $out_dir/merged/SLC/$date; mv /tmp/$date /tmp/merged/SLC
    done
    files1="/tmp/merged/SLC/????????/*.xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files1

elif [[ $job_name == *"unwrap"* && $job_name != *"miaplpy"* ]]; then

    # reference
    distribute_reference $out_dir
    
    # merged/interferograms       
    pair_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _igram_unw_ '{printf "%s\n",$2}' | sort -n | uniq) )
    mkdir -p /tmp/merged/interferograms
    for pair in "${pair_list[@]}"; do
        distribute.bash $out_dir/merged/interferograms/$pair; mv /tmp/$pair /tmp/merged/interferograms
    done
    files1="/tmp/merged/interferograms/????????_????????/*.xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files1

elif [[ $job_name == *"crop"* ]]; then

    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n",$NF}' ) )
    mkdir -p /tmp/SLC
    for date in "${date_list[@]}"; do
        distribute.bash $out_dir/SLC/$date; mv /tmp/$date /tmp/SLC
    done
    files1="/tmp/SLC/????????/*.xml"
    old=$out_dir
    sed -i "s|$old|/tmp|g" $files1

elif [[ $job_name == *"geo2rdr_coarseResamp"* ]]; then

    # cropped reference and secondarys
    ref_date=( $(awk '{printf "%s\n",$3}' $out_dir/run_files/run_02_reference | awk -F _ '{printf "%s\n",$NF}' ) )
    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n",$NF}' ) )
    mkdir -p /tmp/SLC_crop
    distribute.bash $out_dir/SLC_crop/$ref_date; mv /tmp/$ref_date /tmp/SLC_crop
    for date in "${date_list[@]}"; do
        distribute.bash $out_dir/SLC_crop/$date; mv /tmp/$date /tmp/SLC_crop
    done

    files="/tmp/SLC_crop/*/*.xml"
    old=$out_dir 
    sed -i "s|$old|/tmp|g" $files
    
    # geom_reference
    mkdir -p /tmp/merged
    distribute.bash $out_dir/merged/geom_reference; mv /tmp/geom_reference /tmp/merged

elif [[ $job_name == *"refineSecondaryTimin"* ]]; then

    mkdir -p /tmp/SLC_crop
    mkdir -p /tmp/coregSLC/Coarse
    
    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n",$NF}' |  sort -n | uniq ) )
    for date in "${date_list[@]}"; do
        distribute.bash $out_dir/SLC_crop/$date; mv /tmp/$date /tmp/SLC_crop
        distribute.bash $out_dir/coregSLC/Coarse/$date; mv /tmp/$date /tmp/coregSLC/Coarse
    done

    files1="/tmp/SLC_crop/*/*.xml"
    files2="/tmp/coregSLC/Coarse/*/*.xml"
    old=$out_dir 
    sed -i "s|$old|/tmp|g" $files1
    sed -i "s|$old|/tmp|g" $files2

elif [[ $job_name == *"fineResamp"* ]]; then

    mkdir -p /tmp/SLC_crop
    mkdir -p /tmp/coregSLC/Coarse
    mkdir -p /tmp/offsets
    
    ref_date=( $(awk '{printf "%s\n",$3}' $out_dir/run_files/run_02_reference | awk -F _ '{printf "%s\n",$NF}' ) )
    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | grep config_fineResamp | awk -F _ '{printf "%s\n",$NF}' ) )

    #cp -r $out_dir/SLC_crop/$ref_date /tmp/SLC_crop
    distribute.bash $out_dir/SLC_crop/$ref_date; mv /tmp/$ref_date /tmp/SLC_crop
    
    for date in "${date_list[@]}"; do
        distribute.bash $out_dir/SLC_crop/$date; mv /tmp/$date /tmp/SLC_crop
        distribute.bash $out_dir/coregSLC/Coarse/$date; mv /tmp/$date /tmp/coregSLC/Coarse
        distribute.bash $out_dir/offsets/$date; mv /tmp/$date /tmp/offsets
    done

    files1="/tmp/SLC_crop/*/*.xml"
    files2="/tmp/coregSLC/Coarse/*/*.xml"
    files3="/tmp/offsets/*/*.xml"
    old=$out_dir 
    sed -i "s|$old|/tmp|g" $files1
    sed -i "s|$old|/tmp|g" $files2
    sed -i "s|$old|/tmp|g" $files3

elif [[ $job_name == *"grid_baseline"* ]]; then

    mkdir -p /tmp/merged/SLC
           
    ref_date=( $(awk '{printf "%s\n",$3}' $out_dir/run_files/run_02_reference | awk -F _ '{printf "%s\n",$NF}' ) )
    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n",$NF}' ) )
    
    date_list+=($ref_date)
    #date_list=( $(echo "${date_list[@]}" | sort -n | uniq) )
    date_list=( $(printf "%s\n" ${date_list[@]} | sort -n | uniq) )

    for date in "${date_list[@]}"; do
        distribute.bash $out_dir/merged/SLC/$date/; mv /tmp/$date /tmp/merged/SLC
    done

elif [[ $job_name == *"run_09_igram"* ]]; then

    mkdir -p /tmp/merged/SLC
    mkdir -p /tmp/SLC_crop
    
    ref_date=( $(awk '{printf "%s\n",$3}' $out_dir/run_files/run_02_reference | awk -F _ '{printf "%s\n",$NF}' ) )
    date_list=( $(awk '{printf "%s\n",$3}' $batch_file | awk -F _ '{printf "%s\n%s\n",$(NF-1),$NF}' ) )
    
    date_list+=($ref_date)
    date_list=( $(printf "%s\n" ${date_list[@]} | sort -n | uniq) )


    for date in "${date_list[@]}"; do
        distribute.bash $out_dir/merged/SLC/$date/; mv /tmp/$date /tmp/merged/SLC
        distribute.bash $out_dir/SLC_crop/$date/; mv /tmp/$date /tmp/SLC_crop
    done

elif [[ $distribute_file ]]; then
    distribute.bash $distribute_file

fi

echo -e "\ncopy_data_to_tmp.bash: after copy-to-tmp:\n `df -h /tmp`"

