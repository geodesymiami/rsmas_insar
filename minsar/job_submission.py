#!/usr/bin/env python3
# Author: Sara Mirzaee, Joshua Zahner

"""
Functions related to batch job submission.
Should be run with a file containing jobs to submit as a batch.
Optional parameters for job submission are, --memory, --walltime, and --queuename.
Generates job scripts, runs them, and waits for output files to be written before exiting.


This script has functions to support submitting two different job types: a script as a job or a batch file consisting of
multiple parallel tasks. submitting a script as a job is done calling the function: submit_script
However submitting a batch file (calling submit_batch_jobs) can be done in 5 different ways with or without launcher.
Two environmental variables have to be set: JOB_SUBMISSION_SCHEME and QUEUENAME  (set in '~/accounts/platforms_defaults.bash')
QUEUENAME has defaults based on platforms. comment/uncomment or introduce a new one
JOB_SUBMISSION_SCHEME: it can have one of these options:

singletask                     ---> submit each task of a batch file separately in a job
multitask_singleNode           ---> distribute tasks of a batch file into jobs with one node
multitask_multiNode            ---> submit tasks of a batch file in one job with required number of nodes
launcher_multitask_singleNode  ---> distribute tasks of a batch file into jobs with one node, submit with launcher
launcher_multitask_multiNode   ---> submit tasks of a batch file in one job with required number of nodes using launcher

"""

import os
import sys
import subprocess
import argparse
import time
import glob
import numpy as np
from minsar.objects import message_rsmas
import warnings
import minsar.utils.process_utilities as putils
import re

warnings.filterwarnings("ignore", category=FutureWarning)


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
    group.add_argument("--memory", dest="memory", metavar="MEMORY (KB)",
                       help="Amount of memory to allocate, specified in kilobytes")
    group.add_argument("--walltime", dest="wall_time", metavar="WALLTIME (HH:MM)",
                       help="Amount of wall time to use, in HH:MM format")
    group.add_argument("--queuename", dest="queue", metavar="QUEUE", help="Name of queue to submit job to")
    group.add_argument("--outdir", dest="out_dir", default='run_files', metavar="OUTDIR",
                       help="output directory for run files")
    group.add_argument('--numBursts', dest='num_bursts', type=int, metavar='number of bursts',
                            help='number of bursts to calculate walltime')

    return parser


def parse_arguments(args):
    """
    Parses command line arguments into namespace.
    :param args: Arguments to parse
    :return: Namespace with submission parameters (from command line arguments or defaults)
    """
    parser = create_argument_parser()
    job_params = parser.parse_args(args)
    job_params.queue = os.getenv("QUEUENAME")

    scratch_dir = os.getenv('SCRATCHDIR')

    # default queue name is based on scheduler
    if not job_params.queue:
        if scheduler == "LSF":
            job_params.queue = "general"
        if scheduler == "PBS":
            job_params.queue = "batch"
        if scheduler == 'SLURM':
           job_params.queue = "skx-normal"

    job_params.file = os.path.abspath(job_params.file)
    job_params.work_dir = os.path.join(scratch_dir,
                                       job_params.file.rsplit(os.path.basename(scratch_dir))[1].split('/')[1])

    if job_params.out_dir == 'run_files':
        job_params.out_dir = os.path.join(job_params.work_dir, job_params.out_dir)

    job_params.custom_template_file = glob.glob(job_params.work_dir + '/*.template')[0]

    return job_params


class JOB_SUBMIT:
    """
        A class representing the job submission object
    """

    def __init__(self, inps):
        for k in inps.__dict__.keys():
            setattr(self, k, inps.__dict__[k])

        self.platform_name = os.getenv("PLATFORM_NAME")
        self.scheduler = os.getenv("JOBSCHEDULER")
        self.number_of_cores_per_node = int(os.getenv('NUMBER_OF_CORES_PER_NODE'))
        self.number_of_threads_per_core = int(os.getenv('NUMBER_OF_THREADS_PER_CORE'))
        self.submission_scheme = os.getenv('JOB_SUBMISSION_SCHEME')
        self.max_jobs_per_queue = os.getenv('MAX_JOBS_PER_QUEUE')
        self.max_memory_per_node = os.getenv('MAX_MEMORY_PER_NODE')

        if not 'num_bursts' in inps:
            self.num_bursts = None
        if not 'wall_time' in inps:
            self.wall_time = None
        if not 'memory' in inps:
            self.memory = None
        if not 'queue' in inps:
            self.queue = os.getenv('QUEUENAME')
        if not 'out_dir' in inps:
            self.out_dir = '.'

        self.default_memory = None
        self.default_wall_time = None
        self.default_num_threads = None

        self.email_notif = True
        self.job_files = []

    def submit_script(self, job_name, job_file_name, argv, email_notif=None):
        """
        Submits a single script as a job. (compare to submit_batch_jobs for several tasks given in run_file)
        :param job_name: Name of job.
        :param job_file_name: Name of job file.
        :param argv: Command line arguments for running job.
        :param email_notif: If email notifications should be on or not. Defaults to true.
        :return job number of the script that was submitted
        """
        if not os.path.isdir(self.work_dir):
            if os.path.isfile(self.work_dir):
                os.remove(self.work_dir)
            os.makedirs(self.work_dir)

        if not email_notif is None:
            self.email_notif = email_notif

        command_line = os.path.basename(argv[0]) + " "
        command_line += " ".join(flag for flag in argv[1:] if flag != "--submit")

        self.get_memory_walltime(job_file_name, job_type='script')

        self.job_files = []

        self.write_single_job_file(job_name, job_file_name, command_line, work_dir=self.work_dir)

        self.submit_and_check_job_status(self.job_files, work_dir=self.work_dir)

        return

    def submit_batch_jobs(self, batch_file=None, email_notif=None):
        """
        submit jobs based on scheduler
        :param batch_file: batch job name
        :param email_notif: If email notifications should be on or not. Defaults to true.
        :return: True if running on a cluster
        """
        if batch_file is None:
            batch_file = self.file

        if not email_notif is None:
            self.email_notif = email_notif

        message_rsmas.log(self.work_dir, 'job_submission.py {a} --outdir {b}'.format(a=batch_file, b=self.out_dir))

        supported_platforms = ['pegasus', 'STAMPEDE2', 'COMET', 'eos_sanghoon', 'beijing_server', 'deqing_server',
                               'glic_gfz', 'mefe_gfz']

        self.job_files = []

        if os.getenv('PLATFORM_NAME') in supported_platforms:
            print('\nWorking on a {} machine ...\n'.format(os.getenv('JOBSCHEDULER')))

            self.get_memory_walltime(batch_file, job_type='batch')

            with open(batch_file, 'r') as f:
                tasks = f.readlines()
                number_of_tasks = len(tasks)

            number_of_nodes = np.int(np.ceil(number_of_tasks * float(self.default_num_threads) / (
                    (self.number_of_cores_per_node - 1) * self.number_of_threads_per_core)))

            if 'singletask' in self.submission_scheme:

                self.write_batch_singletask_jobs(batch_file)

            elif 'multitask_multiNode' in self.submission_scheme or number_of_nodes == 1:

                job_name = os.path.basename(batch_file)

                job_file_lines = self.get_job_file_lines(job_name, batch_file, number_of_tasks=len(tasks),
                                                         number_of_nodes=number_of_nodes, work_dir=self.out_dir)

                batch_file_name = batch_file + '_0'

                self.job_files.append(self.add_tasks_to_job_file_lines(job_file_lines, tasks, batch_file=batch_file_name))

            elif 'multitask_singleNode' in self.submission_scheme:

                self.split_jobs(batch_file, tasks, number_of_nodes)

            self.submit_and_check_job_status(self.job_files, work_dir=self.out_dir)

            return True

        else:
            print('\nWorking on a single machine ...\n')

            with open(batch_file, 'r') as f:
                command_lines = f.readlines()
                for command_line in command_lines:
                    os.system(command_line)

            return False

    def submit_single_job(self, job_file_name, work_dir):
        """
        Submit a single job (to bsub or qsub). Used by submit_jobs_individually and submit_job_with_launcher and submit_script.
        :param job_file_name: Name of job file to submit.
        :return: Job number of submission
        """

        # use bsub or qsub to submit based on scheduler
        if self.scheduler == "LSF":
            command = "bsub < " + os.path.join(work_dir, job_file_name)
        elif self.scheduler == "PBS":
            command = "qsub < " + os.path.join(work_dir, job_file_name)
        elif self.scheduler == 'SLURM':
            hostname = subprocess.Popen("hostname", shell=True, stdout=subprocess.PIPE).stdout.read().decode("utf-8")
            if hostname.startswith('login') or hostname.startswith('comet'):
                command = "sbatch {}".format(os.path.join(work_dir, job_file_name))
            else:
                # In case we are in compute note, only one job allowed at a time
                job_num = '{}_99999'.format(job_file_name.split('_')[1])
                command = "srun {} > {} 2>{} ".format(os.path.join(work_dir, job_file_name),
                                                      os.path.join(work_dir, job_file_name.split('.')[0] +
                                                                   '_{}.o'.format(job_num)),
                                                      os.path.join(work_dir, job_file_name.split('.')[0] +
                                                                   '_{}.e'.format(job_num)))
        else:
            raise Exception("ERROR: scheduler {0} not supported".format(self.scheduler))

        try:
            output_job = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)

        except subprocess.CalledProcessError as grepexc:
            print("error code", grepexc.returncode, grepexc.output)

        try:
            job_number = re.findall('\d+', output_job.decode("utf-8"))
            job_number = str(max([int(x) for x in job_number]))

        except:
            job_number = job_num

        print("{0} submitted as {1} job #{2}".format(job_file_name, self.scheduler, job_number))

        return job_number

    def write_single_job_file(self, job_name, job_file_name, command_line, work_dir=None):
        """
        Writes a job file for a single job.
        :param job_name: Name of job.
        :param job_file_name: Name of job file.
        :param command_line: Command line containing process to run.
        :param work_dir: working or output directory
        """

        # get lines to write in job file
        job_file_lines = self.get_job_file_lines(job_name, job_file_name, work_dir=work_dir)
        job_file_lines.append("\nfree")
        job_file_lines.append("\n" + command_line + "\n")

        # write lines to .job file
        job_file_name = "{0}.job".format(job_file_name)
        with open(os.path.join(work_dir, job_file_name), "w+") as job_file:
            job_file.writelines(job_file_lines)

        self.job_files.append(job_file_name)
        return

    def write_batch_singletask_jobs(self, batch_file):
        """
        Iterates through jobs in input file and writes a job file for each job using the specified scheduler. This function
        is used for batch jobs in pegasus (LSF) to split the tasks into multiple jobs
        :param batch_file: File containing batch of jobs for which we are creating job files.
        :return: List of job file names.
        """
        with open(batch_file) as input_file:
            job_list = input_file.readlines()

        for i, command_line in enumerate(job_list):
            job_file_name = os.path.abspath(batch_file).split(os.sep)[-1] + "_" + str(i)
            self.write_single_job_file(job_file_name, job_file_name, command_line, work_dir=self.out_dir)

        return

    def submit_and_check_job_status(self, job_files, work_dir=None):
        """
        Writes a single job file for launcher to submit as array. This is used to submit jobs in slurm or sge where launcher
        is available (compare to submit_jobs_individually used on pegasus with LSF)
        :return:
        :param batch_file: File containing tasks that we are submitting.
        :param work_dir: the directory to check outputs and error files of job
        """

        job_numbers = []
        jobs_out = []
        jobs_err = []

        for job_file_name in job_files:
            os.system('chmod +x {}'.format(os.path.join(work_dir, job_file_name)))
            job_num = self.submit_single_job(job_file_name, work_dir)
            out = os.path.join(work_dir, "{}_{}.o".format(job_file_name.split('.')[0], job_num))
            err = os.path.join(work_dir, "{}_{}.e".format(job_file_name.split('.')[0], job_num))
            job_numbers.append(job_num)
            jobs_out.append(out)
            jobs_err.append(err)

        i = 0
        wait_time_sec = 60
        total_wait_time_min = 0
        time.sleep(5)

        if self.scheduler == 'SLURM':
            job_status_file = os.path.join(work_dir, 'job_status')
            for job_number, job_file_name in zip(job_numbers, job_files):
                job_stat = 'wait'
                while job_stat == 'wait':
                    os.system('sacct --format="State"   -j {} > {}'.format(job_number, job_status_file))
                    time.sleep(2)
                    with open(job_status_file, 'r') as stat_file:
                        status = stat_file.readlines()
                        if len(status) < 3:
                            continue
                    if 'PENDING' in status[2] or 'RUNNING' in status[2]:
                        print("Waiting for job {} output file after {} minutes".format(job_file_name,
                                                                                       total_wait_time_min))
                        total_wait_time_min += wait_time_sec / 60
                        time.sleep(wait_time_sec - 2)
                        i += 1
                    elif 'COMPLETED' in status[2]:
                        job_stat = 'complete'
                    elif 'TIMEOUT' in status[2]:
                        job_stat = 'timeout'
                        # need to adjust wall time and rerun job (can the new job number be added to list ?)
                        #wall_time = putils.extract_walltime_from_job_file(job_file_name)
                        #new_wall_time = multiply_walltime(wall_time, factor=2)
                        raise RuntimeError('Error: {} job timed out with Error'.format(job_file_name))
                    else:
                        job_stat = 'failed'
                        raise RuntimeError('Error: {} job was terminated with Error'.format(job_file_name))
        else:

            for out, job_file_name in zip(jobs_out, job_files):
                while not os.path.exists(out):
                    print("Waiting for job {} output file after {} minutes".format(job_file_name, total_wait_time_min))
                    total_wait_time_min += wait_time_sec / 60
                    time.sleep(wait_time_sec)
                    i += 1

        for errfile, job_file_name in zip(jobs_err, job_files):
            error_files = glob.glob(errfile + '*')
            for err in error_files:
                job_exit1 = check_words_in_file(errfile, 'Segmentation fault')
                job_exit2 = check_words_in_file(errfile, 'Aborted')
                if job_exit1 or job_exit2:
                    raise RuntimeError('Error: Segmentation fault or Aborted job: {err}')

        return

    def split_jobs(self, batch_file, tasks, number_of_nodes):
        """
        splits the batch file tasks into multiple jobs with one node
        :param batch_file:
        :param tasks:
        :param number_of_nodes: Total number of nodes required for all tasks
        :return:
        """

        number_of_jobs = number_of_nodes

        number_of_nodes_per_job = 1

        while number_of_jobs > int(self.max_jobs_per_queue):
            number_of_nodes_per_job = number_of_nodes_per_job + 1
            number_of_jobs = np.ceil(number_of_nodes/number_of_nodes_per_job)

        if number_of_nodes_per_job > 1:
            print('Note: Number of jobs exceed the numbers allowed per queue for jobs with 1 node...\n'
                  'Number of Nodes per job are adjusted to {}'.format(number_of_nodes_per_job))

        number_of_parallel_tasks = int(np.ceil(len(tasks) / number_of_jobs))

        start_lines = np.ogrid[0:len(tasks):number_of_parallel_tasks].tolist()
        end_lines = [x + number_of_parallel_tasks for x in start_lines]
        end_lines[-1] = len(tasks)

        for start_line, end_line in zip(start_lines, end_lines):
            job_count = start_lines.index(start_line)
            batch_file_name = batch_file + '_{}'.format(job_count)
            job_name = os.path.basename(batch_file_name)

            job_file_lines = self.get_job_file_lines(job_name, batch_file_name, number_of_tasks=end_line-start_line,
                                                     number_of_nodes=number_of_nodes_per_job, work_dir=self.out_dir)

            job_file_name = self.add_tasks_to_job_file_lines(job_file_lines, tasks[start_line:end_line],
                                                             batch_file=batch_file_name)

            self.job_files.append(job_file_name)

        return

    def get_memory_walltime(self, job_name, job_type='batch'):
        """
        get memory, walltime and number of threads for the job from job_defaults.cfg
        :param job_name: the job file name
        :param job_type: 'batch' or 'script'
        """

        config = putils.get_config_defaults(config_file='job_defaults.cfg')

        if job_type == 'batch':
            step_name = '_'
            step_name = step_name.join(job_name.split('/')[-1].split('_')[2::])
        else:
            step_name = job_name

        if self.memory in [None, 'None']:
            if step_name in config:
                self.default_memory = config[step_name]['memory']
            else:
                self.default_memory = config['DEFAULT']['memory']
        else:
            self.default_memory = self.memory

        if self.wall_time in [None, 'None']:
            if step_name in config:
                self.default_wall_time = config[step_name]['walltime']
                if config[step_name]['adjust'] == 'True':
                    if self.num_bursts is None:
                        self.num_bursts = putils.get_number_of_bursts(self)
            else:
                self.default_wall_time = config['DEFAULT']['walltime']

            self.default_wall_time = putils.walltime_adjust(self.num_bursts, self.default_wall_time, self.scheduler, adjust=config[step_name]['adjust'])
        else:
            self.default_wall_time = self.wall_time

        if step_name in config:
            self.default_num_threads = config[step_name]['num_threads']
        else:
            self.default_num_threads = config['DEFAULT']['num_threads']

        return

    def get_job_file_lines(self, job_name, job_file_name, number_of_tasks=1, number_of_nodes=1, work_dir=None):
        """
        Generates the lines of a job submission file that are based on the specified scheduler.
        :param job_name: Name of job.
        :param job_file_name: Name of job file.
        :param number_of_tasks: Number of lines in batch file to be supposed as number of tasks
        :param number_of_nodes: Number of nodes based on number of tasks (each node is able to perform 68 tasks)
        :return: List of lines for job submission file
        """

        # directives based on scheduler
        if self.scheduler == "LSF":
            number_of_tasks = number_of_nodes
            prefix = "\n#BSUB "
            shell = "/bin/bash"
            name_option = "-J {0}"
            project_option = "-P {0}"
            process_option = "-n {0}" + prefix + "-R span[hosts={1}]"
            stdout_option = "-o {0}_%J.o"
            stderr_option = "-e {0}_%J.e"
            queue_option = "-q {0}"
            walltime_limit_option = "-W {0}"
            # memory_option = "-R rusage[mem={0}]"
            memory_option = False
            email_option = "-B -u {0}"
        elif self.scheduler == "PBS":
            prefix = "\n#PBS "
            shell = "/bin/bash"
            name_option = "-N {0}"
            project_option = "-A {0}"
            process_option = "-l nodes={0}:ppn={1}"
            stdout_option = "-o {0}_$PBS_JOBID.o"
            stderr_option = "-e {0}_$PBS_JOBID.e"
            queue_option = "-q {0}"
            walltime_limit_option = "-l walltime={0}"
            memory_option = "-l mem={0}"
            email_option = "-m bea" + prefix + "-M {0}"
        elif self.scheduler == 'SLURM':
            prefix = "\n#SBATCH "
            shell = "/bin/bash"
            name_option = "-J {0}"
            project_option = "-A {0}"
            process_option = "-N {0}" + prefix + "-n {1}"
            stdout_option = "-o {0}_%J.o"
            stderr_option = "-e {0}_%J.e"
            queue_option = "-p {0}"
            email_option = "--mail-user={}" + prefix + "--mail-type=fail"
            walltime_limit_option = "-t {0}"
            memory_option = False
        else:
            raise Exception("ERROR: scheduler {0} not supported".format(self.scheduler))

        if self.queue == 'parallel':
            number_of_nodes *= 16

        job_file_lines = [
            "#! " + shell,
            prefix + name_option.format(job_name),
            prefix + project_option.format(os.getenv('JOBSHEDULER_PROJECTNAME'))
        ]
        if self.email_notif:
            job_file_lines.append(prefix + email_option.format(os.getenv("NOTIFICATIONEMAIL")))

        job_file_lines.extend([
            prefix + process_option.format(number_of_nodes, number_of_tasks),
            prefix + stdout_option.format(os.path.join(work_dir, job_file_name)),
            prefix + stderr_option.format(os.path.join(work_dir, job_file_name)),
            prefix + queue_option.format(self.queue),
            prefix + walltime_limit_option.format(self.default_wall_time),
        ])
        if memory_option:
            job_file_lines.extend([prefix + memory_option.format(self.default_memory)], )
            # job_file_lines.extend([prefix + memory_option.format(self.max_memory_per_node)], )

        if self.scheduler == "PBS":
            # export all local environment variables to job
            job_file_lines.append(prefix + "-V")

        if self.queue == 'gpu':
            job_file_lines.append(prefix + "--gres=gpu:4")

        return job_file_lines

    def add_tasks_to_job_file_lines(self, job_file_lines, tasks, batch_file=None):
        """
        complete job file lines based on job submission scheme. if it uses launcher, add launcher specific lines
        :param job_file_lines: raw job file lines from function 'get_job_file_lines'
        :param tasks:number of tasks to be include in this job
        :param batch_file: name of batch file containing tasks
        :return:
        """

        job_file_name = "{0}.job".format(batch_file)

        tasks_with_output = []

        if 'launcher' in self.submission_scheme:
            for line in tasks:
                tasks_with_output.append("{} > {} 2>{}\n".format(line.split('\n')[0],
                                                                 os.path.abspath(batch_file) + '_$LAUNCHER_JID.o',
                                                                 os.path.abspath(batch_file) + '_$LAUNCHER_JID.e'))
            if os.path.exists(batch_file):
                os.remove(batch_file)

            with open(batch_file, 'w+') as batch_f:
                    batch_f.writelines(tasks_with_output)

            job_file_lines.append("\n\nmodule load launcher")

            job_file_lines.append("\nexport OMP_NUM_THREADS={0}".format(self.default_num_threads))
            job_file_lines.append("\nexport LAUNCHER_WORKDIR={0}".format(self.out_dir))
            job_file_lines.append("\nexport LAUNCHER_JOB_FILE={0}\n".format(batch_file))
            if self.platform_name == 'STAMPEDE2':
               job_file_lines.append("export LD_PRELOAD=/home1/apps/tacc-patches/python_cacher/myopen.so\n")
            job_file_lines.append("\n$LAUNCHER_DIR/paramrun\n")

            with open(os.path.join(self.out_dir, job_file_name), "w+") as job_f:
                job_f.writelines(job_file_lines)

        else:

            for count, line in enumerate(tasks):
                tasks_with_output.append("{} > {} 2>{} &\n".format(line.split('\n')[0],
                                                                 os.path.abspath(batch_file) + '_{}.o'.format(count),
                                                                 os.path.abspath(batch_file) + '_{}.e'.format(count)))

            if self.platform_name == 'STAMPEDE2':
               job_file_lines.append("\nexport LD_PRELOAD=/home1/apps/tacc-patches/python_cacher/myopen.so")
        
            job_file_lines.append("\n\nexport OMP_NUM_THREADS={0}".format(self.default_num_threads))

            job_file_lines.append("\n")

            for line in tasks_with_output:
                job_file_lines.append(line)

            job_file_lines.append("\nwait")

            with open(os.path.join(self.out_dir, job_file_name), "w+") as job_f:
                job_f.writelines(job_file_lines)

        return job_file_name


def check_words_in_file(errfile, eword):
    """
    Checks for existence of a specific word in a file
    :param errfile: The file to be checked
    :param eword: The word to search for in the file
    :return: True if the word is in the file
    """

    with open(errfile, 'r') as f:
        lines = f.readlines()

    check_eword = [eword in item for item in lines]

    if np.sum(1*check_eword) > 0:
        return True
    else:
        return False

###################################################################################################


if __name__ == "__main__":
    PARAMS = parse_arguments(sys.argv[1::])

    job_obj = JOB_SUBMIT(PARAMS)
    status = job_obj.submit_batch_jobs()
