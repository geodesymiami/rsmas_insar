#!/bin/bash

# Check if at least one argument is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <template1> <template2> ... <templateN>"
    exit 1
fi

# Create or clear the command.bash file
> command.bash

# Loop through each argument
for template in "$@"; do
    # Remove trailing slash if present
    template=${template%/}
    
    # Write the commands to command.bash
    echo "create_save_hdf5_jobfile.py \$TE/${template}.template ${template}/miaplpy_*/network_* --queue skx-dev --outdir ${template}" >> command.bash
    echo "run_workflow.bash \$TE/${template}.template --jobfile save_hdfeos5_radar.job" >> command.bash
done

echo "Commands written to command.bash"
