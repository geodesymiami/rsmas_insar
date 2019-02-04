#!/usr/bin/env python3
"""
Functions related to batch job submission.
Should be run with a file containing jobs to submit as a batch.
Optional parameters for job submission are --template, --memory, --walltime, and --queuename.
Generates job scripts, runs them, and waits for output files to be written before exiting.
"""

import os
import sys
import subprocess
import argparse
import time
import messageRsmas


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
    Parses command line arguments into namespace.
    :param args: Arguments to parse
    :return: Namespace with submission parameters (from command line arguments or defaults)
    """
    parser = create_argument_parser()
    job_submission_params = parser.parse_args(args)
    scheduler = os.getenv("JOBSCHEDULER")

    # default memory, walltime, and queue name
    if not job_submission_params.memory:
        job_submission_params.memory = 3600
    if not job_submission_params.wall:
        job_submission_params.wall = "4:00"
    if not job_submission_params.queue:
        if scheduler == "LSF":
            job_submission_params.queue = "general"
        if scheduler == "PBS":
            job_submission_params.queue = "batch"

    return job_submission_params


def get_job_file_lines(job_name, scheduler=os.getenv("JOBSCHEDULER"), memory=3600, walltime="4:00", queue=None):
    """
    Generates the lines of a job submission file that are based on the specified scheduler.
    :param job_name: Name of job to write file for
    :param scheduler: Job scheduler to use for running jobs. Defaults based on environment variable $JOBSCHEDULER.
    :param memory: Amount of memory to use. Defaults to 3600 KB.
    :param walltime: Walltime for the job. Defaults to 4 hours.
    :param queue: Name of the queue to which the job is to be submitted. Default is set based on the scheduler.
    :return: List of lines for job submission file
    """

    # directives based on scheduler
    if scheduler == "LSF":
        prefix = "\n#BSUB "
        shell = "/bin/tcsh"
        name_option = "-J {}"
        project_option = "-P {}"
        process_option = "-n {}\n" + prefix + "-R span[hosts={}]"
        stdout_option = "-o {}_%J.o"
        stderr_option = "-e {}_%J.e"
        queue_option = "-q {}"
        if not queue:
            queue = "general"
        walltime_limit_option = "-W {}"
        memory_option = "-R rusage[mem={}]"
        email_option = "-B -u {}"
    if scheduler == "PBS":
        prefix = "\n#PBS "
        shell = "/bin/bash"
        name_option = "-N {}"
        project_option = "-A {}"
        process_option = "-l nodes={}:ppn={}"
        stdout_option = "-o {}_$PBS_JOBID.o"
        stderr_option = "-e {}_$PBS_JOBID.e"
        queue_option = "-q {}"
        if not queue:
            queue = "batch"
        walltime_limit_option = "-l walltime={}"
        walltime += ":00"
        memory_option = "-l mem={}"
        email_option = "-m bea\n" + prefix + "-M {}"

    job_file_lines = [
        "#! " + shell,
        prefix + name_option.format(job_name),
        prefix + project_option.format("insarlab"),
        prefix + email_option.format(os.getenv("NOTIFICATIONEMAIL")),
        prefix + process_option.format(1, 1),
        prefix + stdout_option.format(job_name),
        prefix + stderr_option.format(job_name),
        prefix + queue_option.format(queue),
        prefix + walltime_limit_option.format(walltime),
        prefix + memory_option.format(memory),
    ]

    if scheduler == "PBS":
        job_file_lines.append(prefix + "-V")

    return job_file_lines


def write_job_files(job_filename, scheduler=os.getenv("JOBSCHEDULER"), memory=3600, walltime="4:00", queue=None):
    """
    Iterates through jobs in input file and writes a job file for each job using the specified scheduler.
    :param job_filename: Name of job file that we are creating.
    :param scheduler: Job scheduler to use for running jobs. Defaults based on environment variable $JOBSCHEDULER.
    :param memory: Amount of memory to use. Defaults to 3600 KB.
    :param walltime: Walltime for the job. Defaults to 4 hours.
    :param queue: Name of the queue to which the job is to be submitted. Default is set based on the scheduler.
    :return: List of job file names
    """
    job_files = []

    # work directory to write output files to
    work_dir = os.path.join(os.environ["SCRATCHDIR"], job_filename.split("/")[-3], "run_files")
    os.chdir(work_dir)

    with open(job_filename) as input_file:
        job_list = input_file.readlines()
    for i, file_name in enumerate(job_list):
        job_name = job_file.split("/")[-1] + "_" + str(i)
        job_file_lines = get_job_file_lines(job_name, scheduler, memory, walltime, queue)

        # lines not based on scheduler
        job_file_lines.append("\nfree")
        job_file_lines.append("\ncd " + work_dir)
        job_file_lines.append("\n" + file_name)

        with open(job_name + ".job", "w+") as job_file:
            job_file.writelines(job_file_lines)
            job_files.append(job_file.name)

    return job_files


def submit_jobs_to_bsub(job_files, job_filename, scheduler=os.getenv("JOBSCHEDULER")):
    """
    Submit jobs to bsub and wait for output files to exist before exiting.
    :param job_files: Names of job files to submit
    :param job_filename: Name of job file that we are creating.
    :param scheduler: Job scheduler to use for running jobs. Defaults based on environment variable $JOBSCHEDULER.
    """
    work_dir = os.path.join(os.environ["SCRATCHDIR"], job_filename.split("/")[-3], "run_files")
    os.chdir(work_dir)

    files = []

    for job in job_files:
        if scheduler == "LSF":
            command = "bsub < " + job
        elif scheduler == "PBS":
            command = "qsub < " + job
        else:
            raise Exception("ERROR: scheduler {0} not supported".format(scheduler))

        output = subprocess.check_output(command, shell=True)
        # output second line is in format "Job <job id> is submitted to queue <queue name>"

        if scheduler == "LSF":
            job_number = output.decode("utf-8").split("\n")[0].split("<")[1].split(">")[0]   # works for 'Job <19490923> is submitted to queue <general>.\n'
        elif scheduler == "PBS":
            job_number = output.decode("utf-8").split("\n")[0].split(".")[0]   # extracts number from '7319.eos\n'
            job_number = output.decode("utf-8").split("\n")[0]   # uses '7319.eos\n'
        else:
            raise Exception("ERROR: scheduler {0} not supported".format(scheduler))

        job_name = job.split(".")[0]
        files.append("{}_{}.o".format(job_name, job_number))
        # files.append("{}_{}.e".format(job_name, job_number))

    # check if output files exist
    i = 0
    wait_time_sec = 60
    total_wait_time_min = 0
    while i < len(files):
        if os.path.isfile(files[i]):
            print("Job #{} of {} complete (output file {})".format(i+1, len(files), files[i]))
            i += 1
        else:
            print("Waiting for job #{} of {} (output file {}) after {} minutes".format(i+1, len(files), files[i], total_wait_time_min))
            total_wait_time_min += wait_time_sec/60
            time.sleep(wait_time_sec)


if __name__ == "__main__":
    PARAMS = parse_arguments(sys.argv[1::])
    messageRsmas.log(os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1::]))
    JOBS = write_job_files(PARAMS.file, memory=PARAMS.memory, walltime=PARAMS.wall, queue=PARAMS.queue)
    submit_jobs_to_bsub(JOBS, PARAMS.file)
