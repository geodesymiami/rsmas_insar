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
    group.add_argument("--memory", dest="memory", default=3600, metavar="MEMORY (KB)",
                       help="Amount of memory to allocate, specified in kilobytes")
    group.add_argument("--walltime", dest="wall", default="4:00", metavar="WALLTIME (HH:MM)",
                       help="Amount of wall time to use, in HH:MM format")
    group.add_argument("--queuename", dest="queue", metavar="QUEUE", help="Name of queue to submit job to")
    group.add_argument("--outdir", dest="outdir", default='run_files', metavar="OUTDIR",
                       help="output directory for run files")

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

    # default queue name is based on scheduler
    if not job_submission_params.queue:
        if scheduler == "LSF":
            job_submission_params.queue = "general"
        if scheduler == "PBS":
            job_submission_params.queue = "batch"

    return job_submission_params


def get_job_file_lines(job_name, job_file_name, email_notif, scheduler=None, memory=3600, walltime="4:00", queue=None):
    """
    Generates the lines of a job submission file that are based on the specified scheduler.
    :param job_name: Name of job.
    :param job_file_name: Name of job file.
    :param email_notif: If email notifications should be on or not.
    :param scheduler: Job scheduler to use for running jobs. Defaults based on environment variable JOBSCHEDULER.
    :param memory: Amount of memory to use. Defaults to 3600 KB.
    :param walltime: Walltime for the job. Defaults to 4 hours.
    :param queue: Name of the queue to which the job is to be submitted. Default is set based on the scheduler.
    :return: List of lines for job submission file
    """
    if not scheduler:
        scheduler=os.getenv("JOBSCHEDULER")

    # directives based on scheduler
    if scheduler == "LSF":
        prefix = "\n#BSUB "
        shell = "/bin/tcsh"
        name_option = "-J {0}"
        project_option = "-P {0}"
        process_option = "-n {0}" + prefix + "-R span[hosts={1}]"
        stdout_option = "-o {0}_%J.o"
        stderr_option = "-e {0}_%J.e"
        queue_option = "-q {0}"
        if not queue:
            queue = "general"
        walltime_limit_option = "-W {0}"
        memory_option = "-R rusage[mem={0}]"
        email_option = "-B -u {0}"
    elif scheduler == "PBS":
        prefix = "\n#PBS "
        shell = "/bin/bash"
        name_option = "-N {0}"
        project_option = "-A {0}"
        process_option = "-l nodes={0}:ppn={1}"
        stdout_option = "-o {0}_$PBS_JOBID.o"
        stderr_option = "-e {0}_$PBS_JOBID.e"
        queue_option = "-q {0}"
        if not queue:
            queue = "batch"
        walltime_limit_option = "-l walltime={0}"
        walltime += ":00"
        memory_option = "-l mem={0}"
        email_option = "-m bea" + prefix + "-M {0}"
    else:
        raise Exception("ERROR: scheduler {0} not supported".format(scheduler))

    job_file_lines = [
        "#! " + shell,
        prefix + name_option.format(job_name),
        prefix + project_option.format("insarlab")
    ]
    if email_notif:
        job_file_lines.append(prefix + email_option.format(os.getenv("NOTIFICATIONEMAIL")))
    job_file_lines.extend([
        prefix + process_option.format(1, 1),
        prefix + stdout_option.format(job_file_name),
        prefix + stderr_option.format(job_file_name),
        prefix + queue_option.format(queue),
        prefix + walltime_limit_option.format(walltime),
        prefix + memory_option.format(memory),
    ])

    if scheduler == "PBS":
        job_file_lines.append(prefix + "-V")

    return job_file_lines


def write_single_job_file(job_name, job_file_name, command_line, work_dir, email_notif, scheduler=None,
                          memory=3600, walltime="4:00", queue=None):
    """
    Writes a job file for a single job.
    :param job_name: Name of job.
    :param job_file_name: Name of job file.
    :param command_line: Command line containing process to run.
    :param work_dir: Work directory in which to write job, output, and error files.
    :param email_notif: If email notifications should be on or not.
    :param scheduler: Job scheduler to use for running jobs. Defaults based on environment variable JOBSCHEDULER.
    :param memory: Amount of memory to use. Defaults to 3600 KB.
    :param walltime: Walltime for the job. Defaults to 4 hours.
    :param queue: Name of the queue to which the job is to be submitted. Default is set based on the scheduler.
    """
    if not scheduler:
        scheduler=os.getenv("JOBSCHEDULER")

    # get lines to write in job file
    job_file_lines = get_job_file_lines(job_name, job_file_name, email_notif, scheduler, memory, walltime, queue)
    job_file_lines.append("\nfree")
    job_file_lines.append("\ncd " + work_dir)
    job_file_lines.append("\n" + command_line + "\n")

    # write lines to .job file
    os.chdir(work_dir)
    job_file_name = "{0}.job".format(job_file_name)
    with open(job_file_name, "w+") as job_file:
        job_file.writelines(job_file_lines)


def write_batch_job_files(batch_file, out_dir, email_notif=False, scheduler=None, memory=3600, walltime="4:00", queue=None):
    """
    Iterates through jobs in input file and writes a job file for each job using the specified scheduler.
    :param batch_file: File containing batch of jobs for which we are creating job files.
    :param out_dir: Output directory for run files.
    :param email_notif: If email notifications should be on or not. Defaults to false for batch submission.
    :param scheduler: Job scheduler to use for running jobs. Defaults based on environment variable JOBSCHEDULER.
    :param memory: Amount of memory to use. Defaults to 3600 KB.
    :param walltime: Walltime for the job. Defaults to 4 hours.
    :param queue: Name of the queue to which the job is to be submitted. Default is set based on the scheduler.
    :return: List of job file names.
    """
    if not scheduler:
        scheduler=os.getenv("JOBSCHEDULER")

    project_name = batch_file.split(os.sep)[-3]
    work_dir = os.path.join(os.environ["SCRATCHDIR"], project_name, out_dir)

    with open(batch_file) as input_file:
        job_list = input_file.readlines()
    job_files = []
    for i, command_line in enumerate(job_list):
        job_file_name = batch_file.split(os.sep)[-1] + "_" + str(i)
        write_single_job_file(job_file_name, job_file_name, command_line, work_dir, email_notif,
                              scheduler, memory, walltime, queue)
        job_files.append("{0}.job".format(job_file_name))

    return job_files


def submit_single_job(job_file_name, scheduler=None):
    """
    Submit a single job (to bsub or qsub).
    :param job_file_name: Name of job file to submit.
    :param scheduler: Job scheduler to use for running jobs. Defaults based on environment variable JOBSCHEDULER.
    :return: Job number of submission
    """
    if not scheduler:
        scheduler=os.getenv("JOBSCHEDULER")
    
    # use bsub or qsub to submit based on scheduler
    if scheduler == "LSF":
        command = "bsub < " + job_file_name
    elif scheduler == "PBS":
        command = "qsub < " + job_file_name
    else:
        raise Exception("ERROR: scheduler {0} not supported".format(scheduler))

    output = subprocess.check_output(command, shell=True)

    # get job number to return
    if scheduler == "LSF":
        # works for 'Job <19490923> is submitted to queue <general>.\n'
        job_number = output.decode("utf-8").split("\n")[0].split("<")[1].split(">")[0]
    elif scheduler == "PBS":
        # extracts number from '7319.eos\n'
        job_number = output.decode("utf-8").split("\n")[0].split(".")[0]
        # uses '7319.eos\n'
        job_number = output.decode("utf-8").split("\n")[0]
    else:
        raise Exception("ERROR: scheduler {0} not supported".format(scheduler))

    return job_number


def submit_batch_jobs(job_files, batch_file, out_dir, scheduler=None):
    """
    Submit a batch of jobs (to bsub or qsub) and wait for output files to exist before exiting.
    :param job_files: Names of job files to submit.
    :param batch_file: File containing jobs that we are submitting.
    :param out_dir: Output directory for run files.
    :param scheduler: Job scheduler to use for running jobs. Defaults based on environment variable JOBSCHEDULER.
    """
    if not scheduler:
        scheduler=os.getenv("JOBSCHEDULER")

    work_dir = os.path.join(os.environ["SCRATCHDIR"], batch_file.split(os.sep)[-3], out_dir)
    os.chdir(work_dir)

    files = []

    for job in job_files:
        job_number = submit_single_job(job, scheduler)
        job_file_name = job.split(".")[0]
        files.append("{}_{}.o".format(job_file_name, job_number))
        # files.append("{}_{}.e".format(job_file_name, job_number))

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


def submit_script(job_name, job_file_name, argv, work_dir, walltime, email_notif=True):
    """
    Submits a single script as a job.
    :param job_name: Name of job.
    :param job_file_name: Name of job file.
    :param argv: Command line arguments for running job.
    :param work_dir: Work directory in which to write job, output, and error files.
    :param walltime: Input parameter of walltime for the job.
    :param email_notif: If email notifications should be on or not. Defaults to true.
    """
    command_line = os.path.basename(argv[0]) + " "
    command_line += " ".join(flag for flag in argv[1:] if flag != "--submit")
    write_single_job_file(job_name, job_file_name, command_line, work_dir, email_notif,
                          walltime=walltime, queue=os.getenv("QUEUENAME"))
    submit_single_job("{0}.job".format(job_file_name))
    sys.exit(0)


if __name__ == "__main__":
    PARAMS = parse_arguments(sys.argv[1::])
    messageRsmas.log(os.path.basename(sys.argv[0]) + " " + " ".join(sys.argv[1::]))
    JOBS = write_batch_job_files(PARAMS.file, PARAMS.outdir, memory=PARAMS.memory, walltime=PARAMS.wall, queue=PARAMS.queue)
    submit_batch_jobs(JOBS, PARAMS.file, PARAMS.outdir)
