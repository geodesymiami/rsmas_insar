#!/bin/bash

# Check if at least one argument is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <template1> <template2> ... <templateN>"
    exit 1
fi

# Create or clear the command.bash file
> commands2.bash

# Loop through each argument
for template in "$@"; do
    # Remove trailing slash if present
    template=${template%/}
    
    # Write the commands to command.bash
    #echo "create_save_hdf5_jobfile.py \$TE/${template}.template ${template}/miaplpy_*/network_* --queue skx-dev --outdir ${template}" >> command2.bash
    echo "create_insarmaps_jobfile.py  ${template}/miaplpy_*/network_* --dataset filt*DS" --queue skx-dev >> commands2.bash
    echo "mv insarmaps.job ${template}" >> commands2.bash
    echo "cd ${template}" >> commands2.bash
    echo "run_workflow.bash \$TE/${template}.template --jobfile insarmaps.job" >> commands2.bash
    echo "cd .." >> commands2.bash
done

echo "Commands written to commands2.bash"
