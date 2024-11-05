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
                d.udpmessage({"_textarea": out_line})
                sys.exit()
            elif total_time > maximum_time:
                popen.terminate()
                out_line = '\n\n!!!ERROR!!!\nProcess stopped - reached max time of 5 min (300 sec). Is data input a SAXS/SANS dataset with format (q,I,sigma)?. If data is large (several thousand data points), consider rebinning the data.\n\n'
                d.udpmessage({"_textarea": out_line})
                sys.exit()
            else:
                out_line = '%s\n' % nline_latin
                d.udpmessage({"_textarea": out_line})
            f.write(out_line)
    return out_line

if __name__=='__main__':

    argv_io_string = io.StringIO(sys.argv[1])
    json_variables = json.load(argv_io_string)

    path = os.path.dirname(os.path.realpath(__file__))
    command_to_execute = [path + '/sascombine.py']
    command_to_execute.append('-d')

    ## read Json input
    datas = json_variables['data'] # names of datafile
    data_option = " -d \""
    data_string = ""
    for d in datas:
        datafile = d.split('/')[-1]
        data_option += ' ' + datafile
        data_string += ' ' + datafile
    data_option += "\""
    command_to_execute.append(data_string)
    path_for_output = d.replace(datafile,'')
    path_option = " -p " + path_for_output
    command_to_execute.append('-p')
    command_to_execute.append(path_for_output)

    qmin = json_variables['qmin']
    command_to_execute.append('-qmin')
    command_to_execute.append(qmin)
    
    qmax = json_variables['qmax']
    command_to_execute.append('-qmax')
    command_to_execute.append(qmax)

    N = json_variables['N']
    command_to_execute.append('-N')
    command_to_execute.append(N)

    title_in = json_variables['title']
    title = title_in.replace(' ','_')
    command_to_execute.append('-t')
    command_to_execute.append(title)

    save_option = '-sp -exp'
    command_to_execute.append('-sp')
    command_to_execute.append('-exp')

    ## read checkboxes and related input
    # the Json input for checkboxes only exists if boxes are checked
    # therefore I use try-except to import
    options = '-t %s -N %s -qmin %s -qmax %s' % (title,N,qmin,qmax)
    try:
        dummy = json_variables["range"]
        options += ' -r'
        command_to_execute.append('-r')
    except:
        pass

    try:
        dummy = json_variables['error']
        options += ' -err'
        command_to_execute.append('-err')
    except:
        pass

    try:
        dummy = json_variables['plot_lin']
        options += ' -lin'
        command_to_execute.append('-lin')
    except:
        pass
    try:
        dummy = json_variables['nl']
        options += ' -nl'
        command_to_execute.append('-nl')
    except:
        pass
    try:
        dummy = json_variables['res']
        options += ' -res'
        command_to_execute.append('-res')
    except:
        pass
    try:
        dummy = json_variables['pa']
        options += ' -pa'
        command_to_execute.append('-pa')
    except:
        pass

    ## get output folder
    folder = json_variables['_base_directory'] # output folder dir

    ## messaging
    d = genapp(json_variables)
    
    ## run sascombine

    #command = 'python3 sascombine.py %s %s %s' % (save_option,data_option,options)
    #d.udpmessage({"_textarea":"%s\n\n" % command})
    
    f = open('stdout.dat','w')
    #execute([path + '/sascombine.py',data_option],f)
    command = '/sascombine.py %s %s %s' % (save_option,data_option,options)
    #execute([path + '/sascombine.py',save_option,data_option,options],f)
    #execute([path + '/sascombine.py','-p',path_for_output,'-d','X3_SS_scaled.dat X4_SS_B14pt0_scaled.dat','-sp','-exp','-t',title,'-N',N,'-qmin',qmin,'-qmax',qmax],f)
    #execute([path + '/sascombine.py','-p',path_for_output,'-d',data_string,'-sp','-exp','-t',title,'-N',N,'-qmin',qmin,'-qmax',qmax],f)
    execute(command_to_execute,f)
    f.close()
    #os.system('python3 %s/sascombine.py %s %s %s %s' % (path,save_option,path_option,data_option,options))
    combine_dir = 'output_%s' % title
    #f = open('%s/%s_out.txt' % (combine_dir,title))
    #lines = f.readlines()
    #for line in lines:
    #    d.udpmessage({"_textarea": line})
    #f.close()
    for line in command_to_execute:
        d.udpmessage({"_textarea": ' ' + line})

    ## compress output files to zip file
    os.system('zip -r results_%s.zip %s/*' % (title,combine_dir))
    
    ## generate output
    output = {} # create an empty python dictionary
    output["combinefig"] = "%s/%s/merge_%s.png" % (folder,combine_dir,title)
    output["zip"] = "%s/results_%s.zip" % (folder,title)

    ## send output
    print( json.dumps(output) ) # convert dictionary to json and output

