#!/bin/bash

# Function to display help message
show_help() {
  echo "Usage: $0 [options] <job_file1> <job_file2> ..."
  echo
  echo "Options:"
  echo "  --help    Show this help message and exit"
  echo
  echo "This script removes the stdout and stderr files created by previous runs of SLURM jobs."
  echo "It reads the job files, extracts the paths specified in the #SBATCH -o and #SBATCH -e directives,"
  echo "replaces %J with *, and removes the corresponding files if they exist."
  echo
  echo "Examples:"
  echo "  $0 insarmaps.job"
  echo "  $0 run_files/run_02_*.job"
}

# Check if --help is provided
if [[ "$1" == "--help" ]]; then
  show_help
  exit 0
fi

# Check if at least one job file is provided
if [ $# -lt 1 ]; then
  echo "Error: No job files provided."
  show_help
  exit 1
fi

# Process each job file
for job_file in "$@"; do
  if [ ! -f "$job_file" ]; then
    echo "Error: File '$job_file' not found."
    continue
  fi

  echo "Processing job file: $job_file"

  # Extract the paths from the job file
  output_file=$(grep "^#SBATCH -o" "$job_file" | awk '{print $3}')
  error_file=$(grep "^#SBATCH -e" "$job_file" | awk '{print $3}')

  output_file="${output_file//%J/*}"
  error_file="${error_file//%J/*}"

  #if [ -n "$output_file" ]; then
  #  rm -f $output_file
  #fi

  if [ -n "$error_file" ]; then
    rm -f $error_file
  fi

done
