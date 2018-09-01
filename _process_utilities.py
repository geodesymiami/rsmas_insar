#! /usr/bin/env python2
import os
import sys
import time
import datetime
import glob
import warnings
import subprocess

import pysar
from pysar.utils import readfile
from pysar.utils import writefile
from pysar.utils import ptime
import messageRsmas

###############################################################################
def email_pysar_results(textStr, custom_template, print_msg=True):
    '''
       email results
    '''
    if 'email_pysar' not in custom_template:
      return

    cwd = os.getcwd()
     
    fileList1 = ['velocity.png',\
                 'avgSpatialCoherence.png',\
                 'temporalCoherence.png',\
                 'maskTempCoh.png',\
                 'mask.png',\
                 'demRadar_error.png',\
                 'velocityStd.png',\
                 'geo_velocity.png',\
                 'coherence*.png',\
                 'unwrapPhase*.png',\
                 'rms_timeseriesResidual_quadratic.pdf',\
                 'CoherenceHistory.pdf',\
                 'CoherenceMatrix.pdf',\
                 'bl_list.txt',\
                 'Network.pdf',\
                 'geo_velocity_masked.kmz']

    fileList2 = ['timeseries*.png',\
                 'geo_timeseries*.png']

    if os.path.isdir('PYSAR/PIC'):
       prefix='PYSAR/PIC'

    template_file = glob.glob('PYSAR/*.template')[0]

    i=0
    for fileList in [fileList1, fileList2]:
       attachmentStr = ''
       i=i+1
       for fname in fileList:
           fList = glob.glob(prefix+'/'+fname)
           for fileName in fList:
               attachmentStr = attachmentStr+' -a '+fileName

       if i==1 and len(template_file)>0:
          attachmentStr = attachmentStr+' -a '+template_file

       mailCmd = 'echo \"'+textStr+'\" | mail -s '+cwd+' '+attachmentStr+' '+custom_template['email_pysar']
       command = 'ssh pegasus.ccs.miami.edu \"cd '+cwd+'; '+mailCmd+'\"'
       print(command)
       status = subprocess.Popen(command, shell=True).wait()
       if status is not 0:
          sys.exit('Error in email_pysar_results')

###############################################################################
def email_insarmaps_results(custom_template, print_msg=True):
    '''
       email link to insarmaps.miami.edu
    '''
    if 'email_insarmaps' not in custom_template:
      return

    cwd = os.getcwd()
     
    hdfeos_file = glob.glob(cwd + '/PYSAR/S1*.he5')
    hdfeos_file = glob.glob('./PYSAR/S1*.he5')
    hdfeos_file = hdfeos_file[0]
    hdfeos_name = os.path.splitext(os.path.basename(hdfeos_file))[0]

    textStr = 'http://insarmaps.miami.edu/start/-0.008/-78.0/8"\?"startDataset='+hdfeos_name

    mailCmd = 'echo \"'+textStr+'\" | mail -s Miami_InSAR_results:_'+os.path.basename(cwd)+' '+custom_template['email_insarmaps']
    command = 'ssh pegasus.ccs.miami.edu \" '+mailCmd+'\"'

    print(command)
    status = subprocess.Popen(command, shell=True).wait()
    if status is not 0:
       sys.exit('Error in email_insarmaps_results')
##########################################################################
def submit_job(argv,inps):

   command_line=os.path.basename(argv[0])
   i=1
   while i < len(argv):
         if argv[i] !=  '--bsub':
            command_line = command_line+' '+sys.argv[i]
         i=i+1
   command_line=command_line+'\n'

   projectID='insarlab'

   f = open(inps.work_dir+'/process.job', 'w')
   f.write('#! /bin/tcsh\n')
   f.write('#BSUB -J '+inps.project_name+' \n')
   f.write('#BSUB -B -u '+os.getenv('NOTIFICATIONEMAIL')+'\n')
   f.write('#BSUB -o z_processSentinel_%J.o\n')
   f.write('#BSUB -e z_processSentinel_%J.e\n')
   f.write('#BSUB -n 1\n' )
   if projectID:
      f.write('#BSUB -P '+projectID+'\n')
   f.write('#BSUB -q '+os.getenv('QUEUENAME')+'\n')
   #f.write('#BSUB -W 2:00\n')
   #f.write('#BSUB -R rusage[mem=3700]\n')
   #f.write('#BSUB -R span[hosts=1]\n')
   f.write('cd '+inps.work_dir+'\n')
   f.write(command_line)
   f.close()

   if inps.bsub_flag:
      job_cmd = 'bsub -P insarlab < process.job'
      print('bsub job submission')
      os.system(job_cmd)
      sys.exit(0)

##########################################################################
def submit_insarmaps_job(command_list,inps):

   projectID='insarlab'

   f = open(inps.work_dir+'/PYSAR/insarmaps.job', 'w')
   f.write('#! /bin/tcsh\n')
   f.write('#BSUB -J '+inps.project_name+' \n')
   f.write('#BSUB -o z_insarmaps_%J.o\n')
   f.write('#BSUB -e z_insarmaps_%J.e\n')
   f.write('#BSUB -n 1\n' )
   if projectID:
      f.write('#BSUB -P '+projectID+'\n')
   f.write('#BSUB -q general\n')

   f.write('cd '+inps.work_dir+'/PYSAR\n')
   for item in command_list:
      f.write(item+'\n')
   f.close()
   #import pdb; pdb.set_trace()

   job_cmd = 'bsub < insarmaps.job'
   print('bsub job submission')
   os.system(job_cmd)
   sys.exit(0)
##########################################################################


##########################################################################
def file_len(fname):
    p = subprocess.Popen(['wc', '-l', fname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result, err = p.communicate()
    if p.returncode != 0:
        raise IOError(err)
    return int(result.strip().split()[0])
##########################################################################
def check_error_files_sentinelstack(pattern):
       errorFiles  = glob.glob(pattern)

       elist=[]
       for item in errorFiles:
          if os.path.getsize(item)==0:       # remove zero-size error files
             os.remove(item)
          elif file_len(item)== 0:           # remove zero-lines files (produced by error, need to look for isce code that produces it (not in sentinelStack)
             os.remove(item)
          else:
             elist.append(item)

       # skip non-fatal errors
       error_skip_dict={'FileExistsError: [Errno 17] File exists:' : 'merged/geom_master'}
       error_skip_dict['RuntimeWarning: Mean of empty slice']='warnings.warn'
       for efile in elist:
           for item in error_skip_dict:
              if (item in open(efile).read() and error_skip_dict[item] in open(efile).read()): 
                 sys.stderr.write('Skipped error in: '+efile+'\n')
              else:
                 sys.exit('Error file found: '+efile)
                   #if not ('FileExistsError: [Errno 17] File exists:' in open(fname).read() and 'merged/geom_master' in open(fname).read()): # occurs for CharlestonSenT150
                   #sys.exit('Error file found: '+fname)

##########################################################################
'''
//login4/projects/scratch/insarlab/famelung/CushingSenAT34VV[223] cat run_files/run_5_50_16076639.e
/nethome/swdowinski/sinkhole/anaconda3/lib/python3.5/site-packages/numpy/core/_methods.py:59: RuntimeWarning: Mean of empty slice.
  warnings.warn("Mean of empty slice.", RuntimeWarning)
/nethome/swdowinski/sinkhole/anaconda3/lib/python3.5/site-packages/numpy/core/_methods.py:70: RuntimeWarning: invalid value encountered in double_scalars
  ret = ret.dtype.type(ret / rcount)
/nethome/swdowinski/sinkhole/anaconda3/lib/python3.5/site-packages/numpy/core/_methods.py:82: RuntimeWarning: Degrees of freedom <= 0 for slice
  warnings.warn("Degrees of freedom <= 0 for slice", RuntimeWarning)
/nethome/swdowinski/sinkhole/anaconda3/lib/python3.5/site-packages/numpy/core/_methods.py:94: RuntimeWarning: invalid value encountered in true_divide
  arrmean, rcount, out=arrmean, casting='unsafe', subok=False)
/nethome/swdowinski/sinkhole/anaconda3/lib/python3.5/site-packages/numpy/core/_methods.py:116: RuntimeWarning: invalid value encountered in double_scalars
  ret = ret.dtype.type(ret / rcount)
/nethome/swdowinski/sinkhole/anaconda3/lib/python3.5/site-packages/numpy/lib/function_base.py:655: RuntimeWarning: invalid value encountered in true_divide
  return n/(n*db).sum(), bins
//login4/projects/scratch/insarlab/famelung/CushingSenAT34VV[224] ls
'''

