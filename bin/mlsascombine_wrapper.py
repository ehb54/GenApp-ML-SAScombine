#!/usr/bin/python3

import json
import io
import sys
import os
from genapp3 import genapp
import numpy as np
import time
import subprocess

def execute(command,f):
    argv_io_string = io.StringIO(sys.argv[1])
    json_variables = json.load(argv_io_string)
    d = genapp(json_variables)
    start_time = time.time()
    maximum_output_size = 1000000 # maximum output size in number of characters
    maximum_time = 300
    total_output_size = 0
    popen = subprocess.Popen(command, stdout=subprocess.PIPE,bufsize=1)
    lines_iterator = iter(popen.stdout.readline, b"")
    while popen.poll() is None:
        for line in lines_iterator:
            nline = line.rstrip()
            nline_latin = nline.decode('latin')
            total_output_size += len(nline_latin)
            total_time = time.time() - start_time
            if total_output_size > maximum_output_size:
                popen.terminate()
                out_line = '\n\n!!!ERROR!!!\nProcess stopped - could not find solution. Is data input a SAXS/SANS dataset with format (q,I,sigma)?\n\n'
                message.udpmessage({"_textarea": out_line})
                sys.exit()
            elif total_time > maximum_time:
                popen.terminate()
                out_line = '\n\n!!!ERROR!!!\nProcess stopped - reached max time of 5 min (300 sec). Is data input a SAXS/SANS dataset with format (q,I,sigma)?. If data is large (several thousand data points), consider rebinning the data.\n\n'
                message.udpmessage({"_textarea": out_line})
                sys.exit()
            else:
                out_line = '%s\n' % nline_latin
                message.udpmessage({"_textarea": out_line})
            f.write(out_line)
    return out_line

if __name__=='__main__':
    
    argv_io_string = io.StringIO(sys.argv[1])
    json_variables = json.load(argv_io_string)
    message = genapp(json_variables)

    ## initialize execute command
    path = os.path.dirname(os.path.realpath(__file__))
    command_to_execute = [path + '/mlsascombine.py']

    ## read Json input
    datas = json_variables['data'] # names of datafiles
    data_string = ""
    for d in datas:
        datafile = d.split('/')[-1]
        data_string += ' ' + datafile
    command_to_execute.extend(['-d',data_string]) # data
    path_for_output = d.replace(datafile,'')
    command_to_execute.extend(['-p',path_for_output]) # data path
    qmin = json_variables['qmin']
    qmax = json_variables['qmax']
    command_to_execute.extend(['-qmin',qmin,'-qmax',qmax]) # qmin,qmax
    N = json_variables['N'] # number of points in combined file
    command_to_execute.extend(['-N',N])
    title_in = json_variables['title']
    title = title_in.replace(' ','_') # replace spaces by underscores in title
    command_to_execute.extend(['-t',title]) # title
    command_to_execute.extend(['-sp','-exp']) # save_options: save plot and export

    ## read checkboxes and related input
    # the Json input for checkboxes only exists if boxes are checked
    # therefore I use try-except to import
    try:
        dummy = json_variables["range"]
        command_to_execute.append('-r') # only include overlapping datarange
    except:
        pass
    try:
        dummy = json_variables['error']
        command_to_execute.append('-err') # errors
    except:
        pass
    try:
        dummy = json_variables['plot_lin']
        command_to_execute.append('-lin') # plot on lin q scale (not log q)
    except:
        pass
    try:
        dummy = json_variables['nl']
        command_to_execute.append('-nl') # rebin linearly (not logarithmically)
    except:
        pass
    try:
        dummy = json_variables['res']
        command_to_execute.append('-res') # res
    except:
        pass
    try:
        dummy = json_variables['pa']
        command_to_execute.append('-pa') # plot all
    except:
        pass

    
    ## run sascombine
    out_line = 'running ML-SAScombine\n'
    message.udpmessage({"_textarea": out_line}) 
    f = open('stdout.dat','w')
    execute(command_to_execute,f)
    f.close()

    ## compress output files to zip file
    combine_dir = 'output_%s' % title
    os.system('zip -r results_%s.zip %s/*' % (title,combine_dir))
    
    ## send output to GUI
    output = {} # create an empty python dictionary
    folder = json_variables['_base_directory'] # output folder dir
    output["combinefig"] = "%s/%s/merge_%s.png" % (folder,combine_dir,title)
    output["zip"] = "%s/results_%s.zip" % (folder,title)
    print( json.dumps(output) ) # convert dictionary to json and output

