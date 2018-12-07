#!/usr/bin/env python3
"""
Functions related to batch job submission.
Should be run with a file containing jobs to batch create.
Optional parameters for job submission are --template, --memory, --walltime, and --queuename.
Generates job scripts, runs them, and waits for output files to be written before exiting.
"""

import os
import sys
import subprocess
import argparse
import time

JOB_SUBMISSION_PARAMS = None


def create_argument_parser():
    """
    Creates an argument parser for parsing parameters for batch job submission.
    Required parameter: file to batch create
    Optional parameters: template file, memory, walltime, and queue name
    :return: ArgumentParser object for parsing command line batch job submission
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    group = parser.add_argument_group("Input File", "File/Dataset to display")
    group.add_argument("file", type=str, help="The file to batch create")
    group.add_argument("--template", dest="template", metavar="TEMPLATE FILE", help="The template file with options")
    group.add_argument("--memory", dest="memory", metavar="MEMORY (KB)",
                       help="Amount of memory to allocate, specified in kilobytes")
    group.add_argument("--walltime", dest="wall", metavar="WALLTIME (HH:MM)",
                       help="Amount of wall time to use, in HH:MM format")
    group.add_argument("--queuename", dest="queue", metavar="QUEUE", help="Name of queue to submit job to")

    return parser


def parse_arguments(args):
    """
    Parses command line arguments into global JOB_SUBMISSION_PARAMS namespace.
    :param args: arguments to parse
    """
    global JOB_SUBMISSION_PARAMS
    parser = create_argument_parser()
    JOB_SUBMISSION_PARAMS = parser.parse_args(args)

    # default memory, walltime, and queue name
    if JOB_SUBMISSION_PARAMS.memory is None:
        JOB_SUBMISSION_PARAMS.memory = 3600
    if JOB_SUBMISSION_PARAMS.wall is None:
        JOB_SUBMISSION_PARAMS.wall = "4:00"
    if JOB_SUBMISSION_PARAMS.queue is None:
        JOB_SUBMISSION_PARAMS.queue = "general"


def read_input_file_to_list():
    """
    Reads the input file of jobs to batch create into a list.
    :return: List of jobs to batch create
    """
    with open(JOB_SUBMISSION_PARAMS.file) as file:
        job_list = file.readlines()
    return job_list


def get_job_file_lines(job_name, scheduler="LSF"):
    """
    Returns list of lines for a particular job based on the specified scheduler.
    :param job_name: Name of job to write file for
    :param scheduler: Job scheduler to use for running jobs. Currently supports option PBS and defaults to LSF
    :return:
    """
    # directives based on scheduler
    if scheduler == "PBS":
        prefix = "#PBS "
        shebang = "/bin/bash"
        name_option = "-N {}"
        project_option = "-A {}"
        process_option = "-l nodes={}:ppn={}"
        stdout_option = "-o {}_%J.o"
        stderr_option = "-e {}_%J.e"
        queue_option = "-q {}"
        walltime_limit_option = "-l walltime={}"
        walltime = JOB_SUBMISSION_PARAMS.wall + ":00"
        memory_option = "-l mem={}"
        # email_option = "-m bea\n" + prefix + "-M {}"
    else:
        # scheduler = "LSF"
        prefix = "#BSUB "
        shebang = "/bin/tcsh"
        name_option = "-J {}"
        project_option = "-P {}"
        process_option = "-n {}\n" + prefix + "-R span[hosts={}]"
        stdout_option = "-o {}_%J.o"
        stderr_option = "-e {}_%J.e"
        queue_option = "-q {}"
        walltime_limit_option = "-W {}"
        walltime = JOB_SUBMISSION_PARAMS.wall
        memory_option = "-R rusage[mem={}]"
        # email_option = "-B -u {}"

    job_file_lines = [
        "#! " + shebang,
        "\n" + prefix + name_option.format(job_name),
        "\n" + prefix + project_option.format("insarlab"),
        "\n" + prefix + process_option.format(1, 1),
        "\n" + prefix + stdout_option.format(job_name),
        "\n" + prefix + stderr_option.format(job_name),
        "\n" + prefix + queue_option.format(JOB_SUBMISSION_PARAMS.queue),
        "\n" + prefix + walltime_limit_option.format(walltime),
        "\n" + prefix + memory_option.format(JOB_SUBMISSION_PARAMS.memory),
    ]

    return job_file_lines


def write_job_files(scheduler="LSF"):
    """
    Iterates through jobs in input file and writes a job file for each job using the specified scheduler.
    :param scheduler: Job scheduler to use for running jobs. Currently supports option PBS and defaults to LSF
    :return: List of job file names
    """
    job_files = []
    # work directory to write output files to
    work_dir = "/scratch/projects/insarlab/" + os.getlogin() + "/" + JOB_SUBMISSION_PARAMS.file.split("/")[-3] \
               + "/run_files/"
    os.chdir(work_dir)

    for i, file_name in enumerate(read_input_file_to_list()):
        job_name = JOB_SUBMISSION_PARAMS.file.split("/")[-1] + "_" + str(i)
        job_file_lines = get_job_file_lines(job_name, scheduler)
        # lines not based on scheduler
        job_file_lines.append("\nfree")
        job_file_lines.append("\ncd " + work_dir)
        job_file_lines.append("\n" + file_name)

        with open(job_name + ".job", "w+") as job_file:
            job_file.writelines(job_file_lines)
            job_files.append(job_file.name)

    return job_files


def submit_jobs_to_bsub(job_files):
    """
    Submit jobs to bsub and wait for output files to exist before exiting
    :param job_files: Names of job files to submit
    """
    os.chdir("/scratch/projects/insarlab/" + os.getlogin() + "/" + JOB_SUBMISSION_PARAMS.file.split("/")[-3]
             + "/run_files/")

    files = []

    for job in job_files:
        command = "bsub < " + job
        output = subprocess.check_output(command, shell=True)
        # output second line is in format "Job <job id> is submitted to queue <queue name>"
        job_number = output.decode("utf-8").split("\n")[0].split("<")[1].split(">")[0]
        job_name = job.split(".")[0]
        files.append("{}_{}.o".format(job_name, job_number))
        # files.append("{}_{}.e".format(job_name, job_number))

    # check if output files exist
    i = 0
    min_waiting = 0
    while i < len(files):
        if os.path.isfile(files[i]):
            print("Job #{} of {} complete (output file {})".format(i + 1, len(files), files[i]))
            i += 1
        else:
            print("Waiting for job #{} of {} (output file {}) after {} minutes".format(
                i + 1, len(files), files[i], min_waiting))
            min_waiting += 0.25
            time.sleep(15)


if __name__ == "__main__":
    parse_arguments(sys.argv[1:])
    JOBS = write_job_files()
    submit_jobs_to_bsub(JOBS)
