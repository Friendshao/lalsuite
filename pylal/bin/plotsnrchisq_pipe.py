#!/usr/bin/python

import matplotlib
matplotlib.use('Agg')
import copy
import math
import sys
import os
import socket, time
from optparse import *
import re, string
import exceptions
import glob
import tempfile
import ConfigParser
import urlparse
from types import *
from pylab import *
sys.path.append('/archive/home/channa/opt/pylal/lib64/python2.4/site-packages')
from pylal import viz
from pylal import Fr
sys.path.append('/archive/home/channa/opt/glue/lib64/python2.4/site-packages')
from glue import segments
from glue import segmentsUtils
from glue.ligolw import ligolw
from glue.ligolw import table
from glue.ligolw import lsctables
from glue.ligolw import utils
from pylal import CoincInspiralUtils
from glue import pipeline
from glue import lal


#import matplotlib
#matplotlib.use('Agg')
#from pylab import *
#from pylab import *
#from pylal import viz


sys.path.append('@PYTHONLIBDIR@')

rc('text', usetex=False)

def plotsnrchisq(gpsTime,frameFile,outputPath,inspProcParams):
    for row in inspProcParams:
      if row.param == "--channel-name":
        chanStringBase = row.value
        ifoName = str(row.value).split(":",1)
      if row.param == "--segment-length":
        segLen = eval(row.value)
      if row.param == "--sample-rate":
        sampleRate = eval(row.value)
      if row.param == "--segment-overlap":
        segOverlap = eval(row.value)
      if (row.param == "--chisq-delta") or (row.param == "--minimal-match"):
        chisqDelta = eval(row.value)
      if row.param =="--chisq-bins":
        chisqBins = eval(row.value)
      if row.param == "--trig-start-time":
        trigStart = eval(row.value)

    segLenSec = segLen / sampleRate
    segOverlapSec = segOverlap / sampleRate
    chanString = chanStringBase + "_SNRSQ_0"
    # find the start time of the first channel
    # BE CAREFUL ! it is assumed that the sampling frequency is higher than 200 Hz
    testOnFirstChannel = Fr.frgetvect(frameFile,chanString,-1,0.01,0)
    gpsStart = testOnFirstChannel[1]
    if (trigStart):
      trigPosition = int((trigStart - gpsStart) / (segLenSec -segOverlapSec))
    else: trigPosition = 0

    position = int((eval(gpsTime) - gpsStart) / (segLenSec -segOverlapSec)) \
               - trigPosition
    chanNumber = str(position)
    chanNameSnr = chanStringBase + "_SNRSQ_" + chanNumber
    chanNameChisq = chanStringBase + '_CHISQ_' + chanNumber

    # now, read the data !!
    # The window width should be an input argument maybe ?
    duration = 2.0
    # startWindow = float(gpsTime) - duration/2.
    # squareSnr_tuple = Fr.frgetvect(frameFile,chanNameSnr,startWindow,duration,0)

    squareSnr_tuple = Fr.frgetvect(frameFile,chanNameSnr,-1,segLenSec,0)
    squareChisq_tuple = Fr.frgetvect(frameFile,chanNameChisq,-1,segLenSec,0)
    snr_position = float(gpsTime) - ( float(squareSnr_tuple[1]) + \
                   (segLenSec-segOverlapSec)*position )
    chisq_position = float(gpsTime) - ( float(squareChisq_tuple[1]) + \
                   (segLenSec-segOverlapSec)*position )
    # compute the snr vector
    snr_vector = sqrt(squareSnr_tuple[0])
    snr_time = array(range(0, segLen)) * squareSnr_tuple[3][0] - snr_position
    
  
    # compute the r^2
    rsq_vector = squareChisq_tuple[0]
    chisq_time = squareChisq_tuple[1]

    # compute the normalized chisq
    chisqNorm_vector = rsq_vector/(1 + chisqDelta/chisqBins*squareSnr_tuple[0])
    # Now plot the snr time serie !!
    figure(1)
    
    plot(snr_time,snr_vector)
    xlim(-duration/2., duration/2.)
    xlabel('time (s)',size='x-large')
    ylabel(r'snr',size='x-large')
    grid()
    title(ifoName[0] + ' trigger: ' + gpsTime)
    savefig(ifoName[0] + '_' + str(gpsTime).replace(".","_") + '_snr.png')


    # Now plot the r^2 time serie !!
    # figure(2)
    #plot(chisq_time - chisq_position,rsq_vector)
    #xlim(-duration/2., duration/2.)
    #xlabel('time (s)',size='x-large')
    #ylabel(r'$r^2$',size='x-large')
    #grid(1)
    #title(ifoName + ' trigger: ' + gpsTime)
    #savefig(ifoName + '_' + str(gpsTime).replace(".","_")  + '_rsq.png')

    # Now plot the normalized chisq time serie !!
    #figure(3)
    #plot(chisq_time - chisq_position,chisqNorm_vector)
    #xlim(-duration/2., duration/2.)
    #xlabel('time (s)',size='x-large')
    #ylabel(r'$\chi^2 / (p + \delta^2\rho^2)$',size='x-large')
    #grid(1)
    #title(ifoName + ' trigger: ' + gpsTime)
    #savefig(ifoName + '_' + str(gpsTime).replace(".","_")  + '_chisq.png')



    
##############################################################################
#
#  MAIN PROGRAM
#
##############################################################################
usage = """ %prog [options]
"""

parser = OptionParser( usage )

parser.add_option("-v","--version",action="store_true",default=False,\
    help="display version information and exit")

parser.add_option("-f","--frame-file",action="store",type="string",\
    metavar=" FILE",help="use frame files list FILE")

parser.add_option("-t","--gps",action="store",type="string",\
    metavar=" GPS",help="use gps time GPS")

parser.add_option("-o","--output-path",action="store",type="string",\
    metavar=" PATH",help="use output path PATH")

parser.add_option("-x","--inspiral-xml-file", action="store",type="string", \
    metavar=" XML",help="use inspiral-file")


command_line = sys.argv[1:]
(opts,args) = parser.parse_args()

#################################
# if --version flagged
if opts.version:
  print "$Id: plotsnrchisq_pipe.py,v 1.5 2007/05/14 18:52:45 channa Exp $"
  sys.exit(0)

#################################
# Sanity check of input arguments

if not opts.frame_file:
  print >> sys.stderr, "No frame file specified."
  print >> sys.stderr, "Use --frame-file FILE to specify location."
  sys.exit(1)

if not opts.gps:
  print >> sys.stderr, "No gps time specified."
  print >> sys.stderr, "Use --gps GPS to specify location."
  sys.exit(1)

if not opts.output_path:
  print >> sys.stderr, "No output path time specified."
  print >> sys.stderr, "Use --output-path PATH to specify location."
  sys.exit(1)

doc = utils.load_filename(opts.inspiral_xml_file,None)
proc = table.get_table(doc, lsctables.ProcessParamsTable.tableName)
plotsnrchisq(str(opts.gps),opts.frame_file,opts.output_path,proc)

