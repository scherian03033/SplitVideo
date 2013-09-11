#!/usr/bin/python

# Usage Description
# 
# Watch a long source video file in QuickTime's trim mode (so that you get 
# sub-second information) and make note for each desired clip of ...
#
#   ClipName  - each clip will be saved as ClipName.mov
#   ClipStart - timestamp of first frame desired (hh:mm:ss.ss)
#   ClipEnd   - timestamp of last frame desired
#
# ... in a CSV file where each row represents one clip. The CSV file should 
# have the same file prefix as the source video file.
#
# Run SplitVideo with the name of the source video file as its argument and
# it will create the appropriate AppleScript to get Quicktime to do the 
# splitting and will then invoke that script. When complete, it will move
# the new split videos to a subdirectory called <source_name>_split and will
# move the source video to a subdirectory called DoneSplitting.
#
# Interesting commands required
# import os
# os.system(cmd) where cmd is an applescript invocation command in string form

# Other thought: if I do this entirely within AppleScript, I get drag and drop
# and the ability to choose a file in Finder but I would also have to then
# choose the corresponding csv file and also struggle with time calculations.

import subprocess
import os.path
import sys
import string
import csv
import datetime

#####                         DEBUG CONTROL                              #####
#verbose = True;
verbose = False;

def dbgprt(msg, vb = False):
    if verbose == True or vb == True :
        print msg


#####                      SUPPORTING FUNCTIONS                          #####

# tsToSeconds: take a string in colon-delimited, decimal seconds format
#              and convert it to a total seconds value. Assume that the hours 
#              field is optional.

def tsToSeconds(timestr):
    decSplit = string.split(timestr, '.')
    colSplit = string.split(timestr, ':')

    formatString = "%M:%S"

    if len(decSplit) == 1:
        decSeconds = False
    elif len(decSplit) == 2:
        decSeconds = True
        formatString = formatString + ".%f"
    else:
        print "Badly formatted time string: decimal error", timestr
        sys.exit(-1)

    if len(colSplit) == 2:
        hasHours = False;
    elif len(colSplit) == 3:
        hasHours = True;
        formatString = "%H:" + formatString
    else:
        print "Badly formatted time string: colon error", timestr
        sys.exit(-1)
    
    dbgprt(formatString)

    pt = datetime.datetime.strptime(timestr, formatString)

    totalSeconds = (pt.microsecond / 1000000.0) + pt.second + \
                   pt.minute * 60 + pt.hour * 3600

    return str(totalSeconds)

# makeScript: creates an appleScript command to split the original video from
#             segStart to segEnd into a file called segName.mov. This section
#             does the initial setup regardless of splits.

def makeScript(sourceFile):
    scriptString = "tell application \"Finder\"\n\t"
    scriptString = scriptString + "set _movieFile to ((path to movies folder "
    scriptString = scriptString + "as text) & \"Temp Working:\" & "
    scriptString = scriptString + "\"" + sourceFile + "\")\n\t"
    scriptString = scriptString + "set _workingDir to container of file "
    scriptString = scriptString + "_movieFile as text\n" + "end tell\n\n"
    scriptString = scriptString + "tell application \"System Events\" to set "
    scriptString = scriptString + "_name to name of file _movieFile\n"
    scriptString = scriptString + "tell application \"QuickTime Player\"\n\t"
    scriptString = scriptString + "try\n\t\tactivate\n\t\t"
    scriptString = scriptString + "open _movieFile\n\t\tdelay 1\n\n"
    return scriptString

# updateScript: adds appleScript commands to split the original video from
#               segStart to segEnd into a file called segName.mov. It must
#               perform time calculations to convert the parameters into
#               seconds. 

def updateScript(tgtDir, segName, segStart, segEnd):
    scriptString = "\t\ttrim document _name from " + tsToSeconds(segStart)
    scriptString = scriptString + " to " + tsToSeconds(segEnd) + "\n\t\t"
    scriptString = scriptString + "set the target_file to (_workingDir & "
    scriptString = scriptString + "\"" + tgtDir
    scriptString = scriptString + ":\" & \"" + segName + "\" & \".mov\")"
    scriptString = scriptString + "\n\t\texport document 1 in file "
    scriptString = scriptString + "target_file using settings preset "
    scriptString = scriptString + "\"Movie\"\n\n\t\t"
    scriptString = scriptString + "close document 1 without saving\n\t\t"
    scriptString = scriptString + "delay 1\n\t\topen _movieFile\n\t\tdelay 2"
    scriptString = scriptString + "\n\n"
    return scriptString

# closeScript: adds appleScript commands to terminate the export process and
#              handle any exceptions

def closeScript():
    scriptString = "\tclose document 1\n\n"
    scriptString = scriptString + "\ton error a number b\n\t\tdisplay "
    scriptString = scriptString + "dialog a\n\tend try\n"
    scriptString = scriptString + "end tell"
    return scriptString

#####                          MAIN CODE                                 ##### 

# usage help

if len(sys.argv) == 1:
    print sys.argv[0] + ": <filename_to_split>"
    sys.exit(-1)

for arg in sys.argv:
    dbgprt(arg)

# Acquire file prefix and confirm file existence and valid suffix. Currently
# supports mpg and mov extensions. More can be added as long as QuickTime
# Player supports them.

fileName = sys.argv[1]
fileStuff = string.split(fileName, '.')

dbgprt("filename split length: " + str(len(fileStuff)) + " args: " + \
       str(fileStuff));

if len(fileStuff) != 2 or (fileStuff[1] != "mov" and fileStuff[1] != "mpg"):
    print fileName + ": badly formed filename. Must be <filename>.<mov/mpg>"
    sys.exit(-1)

if not os.path.isfile(fileName):
    print fileName + ": does not exist"
    exit(-1)

filePrefix = fileStuff[0]


# Now find the split instructions file, a csv with the same prefix as the
# source video. Quit if it doesn't exist.

splitFileName = filePrefix + ".csv"

if not os.path.isfile(splitFileName):
    print splitFileName + ": does not exist"
    exit(-1)

# Create target directory if it does not exist

targetDir = filePrefix + "_split"

if not os.path.exists(targetDir):
    os.makedirs(targetDir)

# Create global part of script

aScript = makeScript(fileName)

# Read the instructions file and generate split/export appleScript for each
# row

with open(splitFileName, 'rb') as f:
    rowNum = 1;
    reader = csv.reader(f)

    try:
        for row in reader:
            if len(row) != 3:
                print "row", rowNum, "badly formed"
                sys.exit(-1);
            aScript = aScript + updateScript(targetDir, row[0], row[1], row[2]);
            rowNum += 1;
    except csv.Error as e:
        sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

# Create script cleanup sections

aScript = aScript + closeScript()

# At this point, you can print aScript to generate the script or...
# print aScript

# Replace with call to execute script using osascript

scriptName = filePrefix + ".scpt"
with open(scriptName, "w") as text_file:
    text_file.write(aScript)

from subprocess import call

rc = subprocess.call(["osascript", scriptName ])
print "Return code: ", rc

# Now remove script file. Comment out if you want to see what it did
os.remove(scriptName)
