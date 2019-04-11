#! /usr/bin/env python2
#This program is modified from the software originally written by Scott Baker with 
#the following licence:
#
# Yunjun, Jun 2016: to use this, add $INT_SCR to $PYTHONPATH, and import as below
# import message_rsmas
# or for more simple use (recommend):
# from message_rsmas import log
# from message_rsmas import Message as msg
from __future__ import print_function
import os
import sys
import datetime
import inspect


def Message(msg):
    f = open('log1','a')
    callingFunction  = os.path.basename(inspect.stack()[1][1])
    if isinstance(msg,basestring):
        string = callingFunction + ":   " + msg
        sys.stderr.write(string + '\n')
        f.write(string + "\n")
    elif isinstance(msg,list):
        for msgl in msg:
            string = callingFunction + ":   " + str(msgl)
            sys.stderr.write(string + '\n')
            f.write(string + "\n")
    else:
        # logger.error('Unrecognized date format. Only string and list supported.')
        raise Exception("Unrecognized date format. Only string and list supported.")
    f.close()

def log(msg):
    f = open('log','a')
    callingFunction  = os.path.basename(inspect.stack()[1][1])
    dateStr=datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d:%H%M%S') 
    #dateStr=datetime.datetime.now() 
    string = dateStr + " * " +  msg  
    print(string)
    f.write(string + "\n")
    f.close()

def Status(arg1,arg2):
    callingFunction  = os.path.basename(inspect.stack()[1][1])
    string =  callingFunction + " failed in  " + arg1   
    if (arg2 != 0) : Message( string )
    # FA 6/2015: does not work very well calling (programs dn't stop)
    # calling script does not stop. The perl functions do that what 
    # I thought was the purpose of this.  
    # a work around is the following:
    # eCode=os.system("test2.py qw1")
    # if (eCode != 0): message_rsmas.Message("failed in test2.py"); sys.exit(1)


# perl code that got translated

### Usage: Status "command";
### dies if errors $? are true
#sub Status {
#  $name = Prog_name $0;
#  $command = shift;
#  if ($?){ Message "$command failed in $name"; exit 1;}
#}

### prints message to standard error and file log1
#sub Message {
#  $name = Prog_name $0;
#  open LOG1, ">>log1";
#  print LOG1 "$name @_\n";
#  print STDOUT "+$name @_\n";
#  close(LOG1);
#}

### Usage: Log1 "message"
### prints message to file log1
#sub Log1 {
#  $name = Prog_name $0;
#  open LOG1, ">>log1";
#  print LOG1 "$name @_\n";
#  close(LOG1);
#}

### Usage: Message "message"
### prints message to standard error and file log1
#sub Message {
#  $name = Prog_name $0;
#  open LOG1, ">>log1";
#  print LOG1 "$name @_\n";
#  print STDOUT "+$name @_\n";
#  close(LOG1);
#}

#sub Log {
#  open (LOG,">>log");
#  $date = `date +%Y%m%d:%H%M%S`; ### Example date: 19980121:120505
#  chomp $date;                   ### Remove carriage return at end of date
#  print LOG "$date * @_\n";      ### Print date * command arguments
#  close(LOG);
#}

#sub Log0 {
#  open (LOG,">>log0");
#  $date = `date +%Y%m%d:%H%M%S`; ### Example date: 19980121:120505
#  chomp $date;                   ### Remove carriage return at end of date
#  print LOG "$date * @_\n";      ### Print date * command arguments
#  close(LOG);
#}
