#! /bin/bash

PROJECT_NAME=$(basename "$1" | awk -F ".template" '{print $1}')
exit_status="$?"
if [[ $PROJECT_NAME == "" ]]; then
    echo "Could not compute basename for that file. Exiting. Make sure you have specified an input file as the first argument."
    exit 1;
fi

template_file=$1
if [[ $1 == $PWD ]]; then
   template_file=$PWD/$PROJECT_NAME.template
fi

WORK_DIR=$SCRATCHDIR/$PROJECT_NAME

mkdir -p $WORK_DIR
cd $WORK_DIR

acquisition_mode=$(grep acquisition_mode $template_file  | cut -d '=' -f 2)
if [[ $acquisition_mode != *"stripmap"* ]]; then

    #########################
    ###   topsStack   ###
    #########################

    # run_03_average_baseline`
    files="configs_tmp/config_baseline_*"

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="geom_referenceDir : $PWD"
    new="geom_referenceDir : /tmp"
    sed -i "s|$old|$new|g" $files

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_04_fullBurst_geo2rdr
    files="configs_tmp/config_fullBurst_geo2rdr_*"

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="geom_referenceDir : $PWD"
    new="geom_referenceDir : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_05_fullBurst_resample
    files="configs_tmp/config_fullBurst_resample_*"
    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_07_merge_reference_secondary_slc
    files="configs_tmp/config_merge_[0-9]*"

    old="stack : $PWD"
    new="stack : /tmp"
    sed -i "s|$old|$new|g" $files

    old="inp_reference : $PWD"
    new="inp_reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="dirname : $PWD"
    new="dirname : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_08_generate_burst_igram
    files="configs_tmp/config_generate_igram_*"

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_09_merge_burst_igram
    files="configs_tmp/config_merge_igram_[0-9]*"

    old="stack : $PWD"
    new="stack : /tmp"
    sed -i "s|$old|$new|g" $files

    old="inp_reference : $PWD"
    new="inp_reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="dirname : $PWD"
    new="dirname : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_10_filter_coherence
    files="configs_tmp/config_igram_filt_coh_*"
    old="input : $PWD"
    new="input : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_11_unwrap
    files="configs_tmp/config_igram_unw_*"

    old="ifg : $PWD"
    new="ifg : /tmp"
    sed -i "s|$old|$new|g" $files

    old="coh : $PWD"
    new="coh : /tmp"
    sed -i "s|$old|$new|g" $files

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

else
    #########################
    ###   stripmapStack   ###
    #########################

    # run_01_crop
    files="configs_tmp/config_crop_????????"

    old="input : $PWD"
    new="input : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_04_geo2rdr_coarseResamp
    files="configs_tmp/config_geo2rdr_coarseResamp_????????"

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_07_fineResamp
    files="configs_tmp/config_fineResamp_????????"

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    old="offsets : $PWD"
    new="offsets : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_08_grid_baseline
    files="configs_tmp/config_baselinegrid_????????"

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

    # run_09_igram
    files="configs_tmp/config_igram_????????_????????"

    old="reference : $PWD"
    new="reference : /tmp"
    sed -i "s|$old|$new|g" $files

    old="secondary : $PWD"
    new="secondary : /tmp"
    sed -i "s|$old|$new|g" $files

fi