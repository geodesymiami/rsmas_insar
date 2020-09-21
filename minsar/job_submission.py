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

singleTask                     ---> submit each task of a batch file separately in a job
multiTask_singleNode           ---> distribute tasks of a batch file into jobs with one node
multiTask_multiNode            ---> submit tasks of a batch file in one job with required number of nodes
launcher_multiTask_singleNode  ---> distribute tasks of a batch file into jobs with one node, submit with launcher
launcher_multiTask_multiNode   ---> submit tasks of a batch file in one job with required number of nodes using launcher

"""

import os
import sys
import subprocess
import argparse
import time
import glob
import numpy as np
import math
from minsar.objects import message_rsmas
from minsar.objects.auto_defaults import queue_config_file, supported_platforms
import warnings
import minsar.utils.process_utilities as putils
from datetime import datetime
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
    group.add_argument('--template', dest='custom_template_file', type=str,
                         metavar='template file', help='custom template with option settings.\n')
    group.add_argument("--memory", dest="memory", metavar="MEMORY (KB)",
                       help="Amount of memory to allocate, specified in kilobytes")
    group.add_argument("--walltime", dest="wall_time", metavar="WALLTIME (HH:MM)",
                       help="Amount of wall time to use, in HH:MM format")
    group.add_argument("--queue", dest="queue", metavar="QUEUE", help="Name of queue to submit job to")
    group.add_argument("--outdir", dest="out_dir", default='run_files', metavar="OUTDIR",
                       help="output directory for run files")
    group.add_argument('--numBursts', dest='num_bursts', type=int, metavar='number of bursts',
                            help='number of bursts to calculate walltime')
    group.add_argument('--remora', dest='remora', action='store_true', help='use remora to get job information')

    return parser


def parse_arguments(args):
    """
    Parses command line arguments into namespace.
    :param args: Arguments to parse
    :return: Namespace with submission parameters (from command line arguments or defaults)
    """
    parser = create_argument_parser()
    job_params = parser.parse_args(args)

    try:
        scratch_dir = os.getenv('SCRATCH')
    except:
        scratch_dir = os.getcwd()

    job_params.file = os.path.abspath(job_params.file)
    job_params.work_dir = os.path.join(scratch_dir,
                                       job_params.file.rsplit(os.path.basename(scratch_dir))[1].split('/')[1])

    if job_params.out_dir == 'run_files':
        job_params.out_dir = os.path.join(job_params.work_dir, job_params.out_dir)

    return job_params


class JOB_SUBMIT:
    """
        A class representing the job submission object
    """

    def __init__(self, inps):
        for k in inps.__dict__.keys():
            setattr(self, k, inps.__dict__[k])

        if 'prefix' in inps and inps.prefix == 'stripmap':
            self.stack_path = os.path.join(os.getenv('ISCE_STACK'), 'stripmapStack')
            self.prefix = 'stripmap'
        else:
            self.stack_path = os.path.join(os.getenv('ISCE_STACK'), 'topsStack')
            self.prefix = 'tops'

        self.submission_scheme, self.platform_name, self.scheduler, self.queue_name, \
        self.number_of_cores_per_node, self.number_of_threads_per_core, self.max_jobs_per_queue, \
        self.max_memory_per_node, self.wall_time_factor = set_job_queue_values(inps)

        if not 'num_bursts' in inps or not inps.num_bursts:
            self.num_bursts = None
        if not 'wall_time' in inps or not inps.wall_time:
            self.wall_time = None
        if not 'memory' in inps or not inps.memory:
            self.memory = None
        if not 'queue' in inps or not inps.queue:
            self.queue = self.queue_name
        if not 'out_dir' in inps:
            self.out_dir = '.'
        if not 'remora' in inps:
            self.remora = None

        self.default_memory = None
        self.default_wall_time = None
        self.default_num_threads = None
        if not 'reserve_node' in inps or not inps.reserve_node:
            self.reserve_node = 1

        self.email_notif = True
        self.job_files = []

        try:
            dem_file = glob.glob(self.work_dir + '/DEM/*.wgs84')[0]
            inps.template[inps.prefix + 'Stack.demDir'] = dem_file
        except:
            print('DEM does not exist in {}'.format(self.work_dir + '/DEM'))

        self.inps = inps

    def submit_script(self, job_name, job_file_name, argv, email_notif=None, writeOnly='False'):
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

        self.write_single_job_file(job_name, job_file_name, command_line, work_dir=self.work_dir,
                                   number_of_nodes=self.reserve_node)
        if writeOnly == 'False':
            self.submit_and_check_job_status(self.job_files, work_dir=self.work_dir)

        return

    def write_batch_jobs(self, batch_file=None, email_notif=None):
        """
        creates jobs based on scheduler
        :param batch_file: batch job name
        :param email_notif: If email notifications should be on or not. Defaults to true.
        :return: True if running on a cluster
        """
        if batch_file is None:
            batch_file = self.file

        if not email_notif is None:
            self.email_notif = email_notif

        message_rsmas.log(self.work_dir, 'job_submission.py {a} --outdir {b}'.format(a=batch_file, b=self.out_dir))

        self.job_files = []

        if self.platform_name in supported_platforms:
            print('\nWorking on a {} machine ...\n'.format(self.scheduler))

            self.get_memory_walltime(batch_file, job_type='batch')

            with open(batch_file, 'r') as f:
                tasks = f.readlines()
                number_of_tasks = len(tasks)

            number_of_nodes = np.int(np.ceil(number_of_tasks * float(self.default_num_threads) / (
                    self.number_of_cores_per_node * self.number_of_threads_per_core)))

            if 'singleTask' in self.submission_scheme:

                self.write_batch_singletask_jobs(batch_file)

            elif 'multiTask_multiNode' in self.submission_scheme: # or number_of_nodes == 1:

                batch_file_name = batch_file + '_0'
                job_name = os.path.basename(batch_file_name)

                job_file_lines = self.get_job_file_lines(batch_file, job_name, number_of_tasks=len(tasks),
                                                         number_of_nodes=number_of_nodes, work_dir=self.out_dir)
                self.job_files.append(self.add_tasks_to_job_file_lines(job_file_lines, tasks,
                                                                       batch_file=batch_file_name))

            elif 'multiTask_singleNode' in self.submission_scheme:

                self.split_jobs(batch_file, tasks, number_of_nodes)

        if len(self.job_files) > 0:
            for job_file in self.job_files:
                os.system('chmod +x {}'.format(job_file))

        return

    def submit_batch_jobs(self, batch_file=None):
        """
        submit jobs based on scheduler
        :param batch_file: batch job name
        :param email_notif: If email notifications should be on or not. Defaults to true.
        :return: True if running on a cluster
        """

        if len(self.job_files) > 0:
            self.submit_and_check_job_status(self.job_files, work_dir=self.out_dir)

            return True

        else:
            print('\nWorking on a single machine ...\n')
            system_path = os.getenv('PATH')
            with open(batch_file, 'r') as f:
                command_lines = f.readlines()
                if self.prefix == 'stripmap':
                    cmd = 'export PATH=$ISCE_STACK/stripmapStack:$PATH; '
                else:
                    cmd = 'export PATH=$ISCE_STACK/topsStack:$PATH; '
                for command_line in command_lines:
                    os.system(cmd + command_line)
                    os.environ['PATH'] = system_path

            return False

    def submit_single_job(self, job_file_name, work_dir):
        """
        Submit a single job (to bsub or qsub). Used by submit_jobs_individually and submit_job_with_launcher and submit_script.
        :param job_file_name: Name of job file to submit.
        :return: Job number of submission
        """
        job_num_exists = True
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
                command = "{}".format(os.path.join(work_dir, job_file_name))
                job_num_exists = False
        else:
            raise Exception("ERROR: scheduler {0} not supported".format(self.scheduler))

        output_job = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)

        if job_num_exists:
            job_number = re.findall('\d+', output_job.decode("utf-8"))
            job_number = str(max([int(x) for x in job_number]))
        else:
            job_number = 'None'

        return job_number

    def write_single_job_file(self, job_name, job_file_name, command_line, work_dir=None, number_of_nodes=1):
        """
        Writes a job file for a single job.
        :param job_name: Name of job.
        :param job_file_name: Name of job file.
        :param command_line: Command line containing process to run.
        :param work_dir: working or output directory
        """

        # get lines to write in job file
        job_file_lines = self.get_job_file_lines(job_name, job_file_name, work_dir=work_dir,
                                                 number_of_nodes=number_of_nodes)
        job_file_lines.append("\nfree")
        if self.remora:
            job_file_lines.append('\nmodule load remora')
            job_file_lines.append("\nremora " + command_line + "\n")
        else:
            job_file_lines.append("\n" + command_line + "\n")

        # write lines to .job file
        job_file_name = "{0}.job".format(job_file_name)
        with open(os.path.join(work_dir, job_file_name), "w+") as job_file:
            job_file.writelines(job_file_lines)

        self.job_files.append(job_file_name)
        os.system('chmod +x {}'.format(job_file_name))

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
        time.sleep(2)

        if self.scheduler == 'SLURM':
            rerun_job_files = []
            job_status_file = os.path.join(work_dir, 'job_status')
            for job_number, job_file_name in zip(job_numbers, job_files):
                if not job_number == 'None':
                    job_stat = 'wait'
                    while job_stat == 'wait':
                        os.system('sacct --format="State" -j {} > {}'.format(job_number, job_status_file))
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
                            rerun_job_files.append(job_file_name)
                        else:
                            job_stat = 'failed'
                            raise RuntimeError('Error: {} job was terminated with Error'.format(job_file_name))

            if len(rerun_job_files) > 0:
               for job_file_name in rerun_job_files:
                   wall_time = putils.extract_walltime_from_job_file(job_file_name)
                   new_wall_time = putils.multiply_walltime(wall_time, factor=1.2)
                   putils.replace_walltime_in_job_file(job_file_name, new_wall_time)

                   dateStr=datetime.strftime(datetime.now(), '%Y%m%d:%H-%M')
                   string = dateStr + ': re-running: ' + os.path.basename(job_file_name) + ': ' + wall_time + ' --> ' + new_wall_time

                   with open(self.work_dir + '/run_files/rerun.log', 'a') as rerun:
                      rerun.writelines(string)

               self.submit_and_check_job_status(rerun_job_files, work_dir=self.work_dir)

        else:
            for out, job_file_name in zip(jobs_out, job_files):
                if not 'None' in out:
                    while not os.path.exists(out):
                        print("Waiting for job {} output file after {} minutes".format(job_file_name, total_wait_time_min))
                        total_wait_time_min += wait_time_sec / 60
                        time.sleep(wait_time_sec)
                        # i += 1

        for job_file_name in job_files:
            error_files = glob.glob(job_file_name.split('.')[0] + '*.e')
            for errfile in error_files:
                job_exit = [check_words_in_file(errfile, 'Segmentation fault'),
                            check_words_in_file(errfile, 'Aborted'),
                            check_words_in_file(errfile, 'ERROR'),
                            check_words_in_file(errfile, 'Error')]
                if np.array(job_exit).any():
                    raise RuntimeError('Error terminating job: {}'.format(job_file_name))
                    
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

        number_of_parallel_tasks = int(np.ceil(len(tasks) / number_of_jobs))
        number_of_limited_memory_tasks = int(self.max_memory_per_node*number_of_nodes_per_job/self.default_memory)
        #if ( "run_15_filter_coherence" in batch_file) :
        #    import pdb; pdb.set_trace()

        while number_of_limited_memory_tasks < number_of_parallel_tasks:
            if number_of_jobs < int(self.max_jobs_per_queue):
                number_of_jobs += 1
                number_of_parallel_tasks = int(np.ceil(len(tasks) / number_of_jobs))
            else:
                break

        while number_of_limited_memory_tasks < number_of_parallel_tasks:
            number_of_nodes_per_job = number_of_nodes_per_job + 1
            number_of_limited_memory_tasks = int(self.max_memory_per_node * number_of_nodes_per_job / self.default_memory)

        self.number_of_parallel_tasks_per_node = math.ceil(number_of_parallel_tasks / number_of_nodes_per_job)

        if number_of_nodes_per_job > 1:
            print('Note: Number of jobs exceed the numbers allowed per queue for jobs with 1 node...\n'
                  'Number of Nodes per job are adjusted to {}'.format(number_of_nodes_per_job))

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

        if self.prefix == 'tops' and job_type == 'batch':
            if self.num_bursts is None:
                self.num_bursts = putils.get_number_of_bursts(self.inps)

        if self.num_bursts:
            number_of_bursts = self.num_bursts
        else:
            number_of_bursts = 1

        if self.memory in [None, 'None']:
            if step_name in config:
                c_memory = config[step_name]['c_memory']
                s_memory = config[step_name]['s_memory']
            else:
                c_memory = config['default']['c_memory']
                s_memory = config['default']['s_memory']

            self.default_memory = putils.scale_memory(number_of_bursts, c_memory, s_memory)
        else:
            self.default_memory = self.memory

        if self.wall_time in [None, 'None']:
            if step_name in config:
                c_walltime = config[step_name]['c_walltime']
                s_walltime = config[step_name]['s_walltime']

            else:
                c_walltime = config['default']['c_walltime']
                s_walltime = config['default']['s_walltime']

            self.default_wall_time = putils.scale_walltime(number_of_bursts, self.wall_time_factor,
                                                           c_walltime, s_walltime, self.scheduler)
        else:
            #self.default_wall_time = self.wall_time
            c_walltime = self.wall_time
            s_walltime = '0'

        self.default_wall_time = putils.scale_walltime(number_of_bursts, self.wall_time_factor,
                                                       c_walltime, s_walltime, self.scheduler)

        if step_name in config:
            self.default_num_threads = config[step_name]['num_threads']
        else:
            self.default_num_threads = config['default']['num_threads']

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

        number_of_tasks = number_of_nodes * self.number_of_cores_per_node

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
            #memory_option = "-R rusage[mem={0}]"
            memory_option = "-M {}"
            #memory_option = False
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
            # if number_of_nodes > 1 and number_of_tasks == 1:
            #     number_of_tasks = number_of_nodes * self.number_of_cores_per_node
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
            prefix + name_option.format(os.path.basename(job_name)),
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
            if not 'launcher' in self.submission_scheme:
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
        do_launcher = False
        if self.scheduler == 'SLURM':
            hostname = subprocess.Popen("hostname", shell=True, stdout=subprocess.PIPE).stdout.read().decode("utf-8")
            if not hostname.startswith('login') or not hostname.startswith('comet'):
                do_launcher = True

        job_file_name = "{0}.job".format(batch_file)

        tasks_with_output = []
        if 'launcher' in self.submission_scheme or do_launcher:
            for line in tasks:
                config_file = putils.extract_config_file_from_task_string(line)
                date_string = putils.extract_date_string_from_config_file_name(config_file)
                tasks_with_output.append("{} > {} 2>{}\n".format(line.split('\n')[0],
                                                                 os.path.abspath(batch_file) + '_' + date_string + '_$LAUNCHER_JID.o',
                                                                 os.path.abspath(batch_file) + '_' + date_string + '_$LAUNCHER_JID.e'))
            if os.path.exists(batch_file):
                os.remove(batch_file)

            with open(batch_file, 'w+') as batch_f:
                    batch_f.writelines(tasks_with_output)

            if self.remora:
                job_file_lines.append("\n\nmodule load remora")

            job_file_lines.append("\n\nmodule load launcher")
            #if self.queue in ['gpu', 'rtx', 'rtx-dev']:
            #    job_file_lines.append("\n\nmodule load launcher_gpu")
            #else:
            #    job_file_lines.append("\n\nmodule load launcher")

            job_file_lines.append("\nexport OMP_NUM_THREADS={0}".format(self.default_num_threads))
            job_file_lines.append("\nexport PATH={0}:$PATH".format(self.stack_path))
            job_file_lines.append("\nexport LAUNCHER_WORKDIR={0}".format(self.out_dir))
            job_file_lines.append("\nexport LAUNCHER_PPN={0}\n".format(self.number_of_parallel_tasks_per_node))
            job_file_lines.append("\nexport LAUNCHER_JOB_FILE={0}\n".format(batch_file))
           
            #if self.scheduler == 'SLURM':

               #job_file_lines.append("module load python_cacher \n")
               #job_file_lines.append("export LD_PRELOAD=/home1/apps/tacc-patches/python_cacher/myopen.so\n")

            if self.remora:
                job_file_lines.append("\nremora $LAUNCHER_DIR/paramrun\n")
                job_file_lines.append("\nmv remora_$SLURM_JOB_ID remora_" + os.path.basename(batch_file) + "_$SLURM_JOB_ID\n")

            else:
                job_file_lines.append("\n$LAUNCHER_DIR/paramrun\n")


            with open(os.path.join(self.out_dir, job_file_name), "w+") as job_f:
                job_f.writelines(job_file_lines)

        else:

            for count, line in enumerate(tasks):
                tasks_with_output.append("{} > {} 2>{} &\n".format(line.split('\n')[0],
                                                                 os.path.abspath(batch_file) + '_{}.o'.format(count),
                                                                 os.path.abspath(batch_file) + '_{}.e'.format(count)))

            if self.scheduler == 'SLURM':

               job_file_lines.append("\nexport LD_PRELOAD=/home1/apps/tacc-patches/python_cacher/myopen.so")

            job_file_lines.append("\n\nexport OMP_NUM_THREADS={0}".format(self.default_num_threads))
            job_file_lines.append("\nexport PATH={0}:$PATH".format(self.stack_path))

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


def set_job_queue_values(args):
    
    template = auto_template_not_existing_options(args)
    submission_scheme = template['job_submission_scheme']
    if submission_scheme == 'auto':
        if os.getenv('JOB_SUBMISSION_SCHEME'):
            submission_scheme = os.getenv('JOB_SUBMISSION_SCHEME')
        else:
            submission_scheme = 'launcher_multiTask_singleNode'
    hostname = subprocess.Popen("hostname -f", shell=True, stdout=subprocess.PIPE).stdout.read().decode("utf-8")

    for platform in supported_platforms:
        if platform in hostname:
            platform_name = platform
            break
        else:
            platform_name = None

    if args.queue:
        template['QUEUENAME'] = args.queue
    elif os.getenv('QUEUENAME'):
        template['QUEUENAME'] = os.getenv('QUEUENAME')

    template['WALLTIME_FACTOR'] = os.getenv('WALLTIME_FACTOR')

    check_auto = {'queue_name': template['QUEUENAME'],
                  'number_of_cores_per_node': template['JOB_CPUS_PER_NODE'],
                  'number_of_threads_per_core': template['THREADS_PER_CORE'],
                  'max_jobs_per_queue': template['MAX_JOBS_PER_QUEUE'],
                  'wall_time_factor': template['WALLTIME_FACTOR'],
                  'max_memory_per_node': template['MEM_PER_NODE']}

    for key in check_auto.keys():
        if not check_auto[key] == 'auto':
            if key == 'wall_time_factor':
                check_auto[key] = float(check_auto[key])
            elif not key == 'queue_name':
                check_auto[key] = int(check_auto[key])

    if platform_name in supported_platforms:
        with open(queue_config_file, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith('PLATFORM_NAME'):
                queue_header = lines[0].split()
                break
        for line in lines:
            if not line.startswith('#') and line.startswith(platform_name):
                split_values = line.split()
                default_queue = split_values[queue_header.index('QUEUENAME')]
                if check_auto['queue_name'] == 'auto':
                    check_auto['queue_name'] = default_queue
                if default_queue == check_auto['queue_name']:
                    if check_auto['number_of_cores_per_node'] == 'auto':
                        check_auto['number_of_cores_per_node'] = int(split_values[queue_header.index('JOB_CPUS_PER_NODE')])
                    if check_auto['number_of_threads_per_core'] == 'auto':
                        check_auto['number_of_threads_per_core'] = int(split_values[queue_header.index('THREADS_PER_CORE')])
                    if check_auto['max_jobs_per_queue'] == 'auto':
                        check_auto['max_jobs_per_queue'] = int(split_values[queue_header.index('MAX_JOBS_PER_QUEUE')])
                    if check_auto['max_memory_per_node'] == 'auto':
                        check_auto['max_memory_per_node'] = int(split_values[queue_header.index('MEM_PER_NODE')])
                    if check_auto['wall_time_factor'] == 'auto':
                        check_auto['wall_time_factor'] = float(split_values[queue_header.index('WALLTIME_FACTOR')])

                    break
                else:
                    continue

    if platform_name in ['stampede2', 'frontera', 'comet']:
        scheduler = 'SLURM'
    elif platform_name in ['pegasus']:
        scheduler = 'LSF'
    elif platform_name in ['eos_sanghoon', 'beijing_server', 'deqing_server']:
        scheduler = 'PBS'
    else:
        scheduler = None

    def_auto = [None, 16, 1, 1, 16000, 1]
    i = 0
    for key, value in check_auto.items():
        if check_auto[key] == 'auto':
            check_auto[key] = def_auto[i]
            i += 1

    out_puts = (submission_scheme, platform_name, scheduler, check_auto['queue_name'], check_auto['number_of_cores_per_node'],
                check_auto['number_of_threads_per_core'], check_auto['max_jobs_per_queue'],
                check_auto['max_memory_per_node'], check_auto['wall_time_factor'])

    return out_puts


def auto_template_not_existing_options(args):

    job_options = ['QUEUENAME', 'JOB_CPUS_PER_NODE', 'THREADS_PER_CORE', 'MAX_JOBS_PER_QUEUE',
                   'WALLTIME_FACTOR', 'MEM_PER_NODE', 'job_submission_scheme']

    if 'custom_template_file' in args:
        from minsar.objects.dataset_template import Template
        template = Template(args.custom_template_file).options

        for option in job_options:
            if not option in template:
                template[option] = 'auto'
    else:
        template = {}
        for option in job_options:
            template[option] = 'auto'

    return template

###################################################################################################


if __name__ == "__main__":
    PARAMS = parse_arguments(sys.argv[1::])

    job_obj = JOB_SUBMIT(PARAMS)
    job_obj.write_batch_jobs()
    status = job_obj.submit_batch_jobs()
