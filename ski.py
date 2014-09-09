#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""A simple client to create a CLA model for the ski game."""

import sys
import random
import logging
from time import sleep

from nupic.frameworks.opf.modelfactory import ModelFactory
from nupic.data.inference_shifter import InferenceShifter

import model_params


yards = 0
totalsize = 80
slopewidth = 21 #31
slopewidthmin = 23
slopewidthmax = 35
variablewidth = False

# True for Random Course, False for repeatable testing data.
UseRNG = True
# True for user wait, False for continuous training/validation.
UsePrompt = False
#True for delayed ski game output, False for no delay
UseDelay = False
DelaySeconds = 0.1
# number of complete training sets to train on
_NUM_TRAINING_SETS = 10



#-----------------------------------------------------------------------------
# Command Prompt Functions
#-----------------------------------------------------------------------------
try:
    import tty, termios
except ImportError:
    # Probably Windows.
    try:
        import msvcrt
    except ImportError:
        # FIXME what to do on other platforms?
        # Just give up here.
        raise ImportError('getch not available')
    else:
        getch = msvcrt.getch
else:
    def getch():
        """getch() -> key character

        Read a single keypress from stdin and return the resulting character. 
        Nothing is echoed to the console. This call will block if a keypress 
        is not already available, but will not wait for Enter to be pressed. 

        If the pressed key was a modifier key, nothing will be detected; if
        it were a special function key, it may return the first character of
        of an escape sequence, leaving additional characters in the buffer.
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


#-----------------------------------------------------------------------------
# skier functions
#-----------------------------------------------------------------------------
def generate_random(choicelist):
    random_choice = random.choice(choicelist)
    return random_choice

def calc_skier_position(skierposition,predicted):
    if predicted > skierposition:
        skierposition = skierposition + 1
    if predicted < skierposition:
        skierposition = skierposition - 1
    return skierposition

def print_slopeline(paddingleft,tree,skier,slopewidth,skierposition,totalsize,yards,printbool):
    """
    This function prints a line of the slope to the screen (stdout).
    The line includes two trees, and a skier.  Occasionally the
    trees are not printed due to a jump.  The width of the slope is
    static for now, and the random number is used to determine how
    far from the left side of the screen the slope begins.
    0--------------t--------S----------t-------------
    """
    treeleft = paddingleft + 1
    leftspace = skierposition - treeleft - 1
    rightspace = slopewidth - leftspace - 1
    treeright = treeleft + slopewidth + 1
    paddingright = totalsize - treeright
    if printbool:
        if(UseDelay == True):
            sleep(DelaySeconds)
        print paddingleft*"." + tree + leftspace*"." + skier + rightspace*"." + tree + paddingright*".", yards

    return {'treeleft': treeleft, 'skierpos': skierposition, 'treeright': treeright}

def print_slopeline_perfect(padding,tree,skier,slopewidth,totalsize,yards,printbool):
    skierposition = padding + 1 + int(round(float(slopewidth)/2))
    paddingleft = padding
    paddingright = totalsize-(paddingleft+1+slopewidth+1)
    if(paddingright > paddingleft) and (slopewidth%2 == 0):
        skierposition = skierposition+1

    return print_slopeline(padding,tree,skier,slopewidth,skierposition,totalsize,yards,printbool)

def print_slopeline_crash(paddingleft,treeloc,slopewidth,totalsize,yards):
    """
    This function prints a line of the slope to the screen (stdout)
    that indicates the skier crashed.
    """
    tree = "|"
    crashedtree = "*"
    treeleft = paddingleft + 1
    treeright = treeleft + slopewidth + 1
    paddingright = totalsize - treeright
    
    if treeloc == 1:
        print paddingleft*"." + crashedtree + slopewidth*"." + tree + paddingright*".", yards 
    elif treeloc == 2:
	print paddingleft*"." + tree + slopewidth*"." + crashedtree + paddingright*".", yards


def print_stats(records, yards):
    """
    This function prints the final stats after a skier has crashed.
    """
    print "Training data sets: ", records, ", Test Run Yards: ", yards
    return 0


#-----------------------------------------------------------------------------
# nupic functions
#-----------------------------------------------------------------------------
def createModel():
  return ModelFactory.create(model_params.MODEL_PARAMS)

def runGame():
  global yards #0
  global totalsize #80
  global slopewidth #21
  global slopewidthmin #23
  global slopewidthmax #35
  global variablewidth #boolean, false
  tree = "|"
  skier = "H"
  minpadding = 0
  maxpadding = totalsize-(slopewidth+2)
  choicelist_drift = [-2, -1, 0, 1, 2]
  choicelist_width = [-2, 0, 2]

  #create NuPIC model
  model = createModel()
  model.enableInference({'predictionSteps': [1], 'predictedField': 'skierpos', 'numRecords': 4000})
  inf_shift = InferenceShifter();
 
  #do training here
  print
  print "================================= Start Training ================================="
  print
  yards = 0
  if (variablewidth):
      for i in xrange(_NUM_TRAINING_SETS):
          for j in xrange(slopewidthmin, slopewidthmax+1):
              for k in xrange((totalsize-j)-1):
                  yards = yards + 1
                  record = print_slopeline_perfect(k, tree, skier, j, totalsize, j, 1)
                  result = inf_shift.shift(model.run(record))
  else:
      for i in xrange(_NUM_TRAINING_SETS): #total training sets
          for j in xrange(maxpadding+1): #one training set
              yards = yards + 1
              record = print_slopeline_perfect(j, tree, skier, slopewidth, totalsize, yards, 1)
              result = inf_shift.shift(model.run(record))

  if(UsePrompt == True):
      print "press any key to continue..."
      getch()

  #check model outputs
  model.disableLearning()
  print
  print "=============================== Validation ========================================"
  print
  yards = 0
  if (variablewidth):
      for j in xrange(slopewidthmin, slopewidthmax+1):
          for k in xrange((totalsize-j)-1):
              record = print_slopeline(k, tree, skier, j, k+2, totalsize, j, 0)
              result = inf_shift.shift(model.run(record))
              inferred = result.inferences['multiStepPredictions'][1]
              predicted = sorted(inferred.items(), key=lambda x: x[1])[-1][0]
              print_slopeline(k, tree, skier, j, int(round(predicted)), totalsize, int(round(predicted)), 1)
  else:
      for i in xrange(maxpadding+1):
          record = print_slopeline(i,tree, skier, slopewidth, i+2, totalsize, yards, 0)
          result = inf_shift.shift(model.run(record))
          inferred = result.inferences['multiStepPredictions'][1]
          predicted = sorted(inferred.items(), key=lambda x: x[1])[-1][0]
          print_slopeline(i, tree, skier, slopewidth, int(round(predicted)), totalsize, int(round(predicted)), 1) 
  if(UsePrompt == True):
      print "press any key to continue..."
      getch()
  
  #do actual run here
  print
  print "=================================== Begin Game ==================================="
  print
  if(UseRNG == True):
      random.seed() #set this again or it will use the NuPIC seed
  yards = 0
  change = 0
  padding = random.randint(minpadding,maxpadding) 
  skierposition = (padding + (slopewidth)/2)
  while True:
    yards = yards + 1
    if (variablewidth):
        change = generate_random(choicelist_width)
        slopewidth = slopewidth + change
        if slopewidth > slopewidthmax:
            slopewidth = slopewidthmax
        if slopewidth < slopewidthmin:
            slopewidth = slopewidthmin

    drift = generate_random(choicelist_drift)
    padding = padding + drift
    if padding > maxpadding:
        padding = maxpadding
    if padding < minpadding:
        padding = minpadding

	padding = padding - (change/2)
    if padding < 0:
        padding = 0
    if (padding + slopewidth + 2) > totalsize:
        padding = totalsize - (slopewidth+2)

    if ((skierposition - (padding+1)) < 1):
        print_slopeline_crash(padding,1,slopewidth,totalsize,yards)
        print_stats(_NUM_TRAINING_SETS, yards)
        break
    if (skierposition - (padding+1) > slopewidth):
        print_slopeline_crash(padding,2,slopewidth,totalsize,yards)
        print_stats(_NUM_TRAINING_SETS, yards)
        break
    
    #pring ski text, get current ski data for NuPIC model
    record = print_slopeline(padding,tree,skier,slopewidth,skierposition,totalsize,yards,1)

    #do NuPIC model ski position calculation
    result = inf_shift.shift(model.run(record))
    inferred = result.inferences['multiStepPredictions'][1]
    predicted = sorted(inferred.items(), key=lambda x: x[1])[-1][0]
    skierposition = calc_skier_position(skierposition, predicted)


if __name__ == "__main__":
  runGame() 


