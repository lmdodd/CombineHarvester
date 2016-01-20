#!/usr/bin/env python

import argparse
import os
import re
import sys
import json
import math
import itertools
import stat
import glob
from array import array
from multiprocessing import Pool
import CombineHarvester.CombineTools.combine.utils as utils
from CombineHarvester.CombineTools.combine.opts import OPTS

from CombineHarvester.CombineTools.combine.CombineToolBase import CombineToolBase

class Impacts(CombineToolBase):
  description = 'Calculate nuisance parameter impacts' 
  requires_root = True

  def __init__(self):
    CombineToolBase.__init__(self)

  def attach_intercept_args(self, group):
    CombineToolBase.attach_intercept_args(self, group)
    group.add_argument('-m', '--mass', required=True)
    group.add_argument('-d', '--datacard', required=True)
    group.add_argument('--redefineSignalPOIs')
    group.add_argument('--name', '-n', default='Test')

  def attach_args(self, group):
    CombineToolBase.attach_args(self, group)
    # group.add_argument('--offset', default=0, type=int,
    #     help='Start the loop over parameters with this offset (default: %(default)s)')
    # group.add_argument('--advance', default=1, type=int,
    #     help='Advance this many parameters each step in the loop (default: %(default)s')
    group.add_argument('--named', metavar='PARAM1,PARAM2,...',
        help=('By default the list of nuisance parameters will be loaded from the input workspace. '
              'Use this option to specify a different list'))
    group.add_argument('--doInitialFit', action='store_true',
        help=('Find the crossings of all the POIs. Must have the output from this before running with --doFits'))
    group.add_argument('--splitInitial', action='store_true',
        help=('In the initial fits generate separate jobs for each POI'))
    group.add_argument('--doFits', action='store_true',
        help=('Actually run the fits for the nuisance parameter impacts, otherwise just looks for the results'))
    group.add_argument('--output', '-o',
        help=('write output json to a file'))
  def run_method(self):
    # offset      = self.args.offset
    # advance     = self.args.advance
    passthru    = self.passthru 
    mh          = self.args.mass
    ws          = self.args.datacard
    name        = self.args.name if self.args.name is not None else ''
    named = []
    if self.args.named is not None:
      named = self.args.named.split(',')
    # Put intercepted args back
    passthru.extend(['-m', mh])
    passthru.extend(['-d', ws])
    pass_str = ' '.join(passthru)
    paramList = []
    if self.args.redefineSignalPOIs is not None:
      poiList = self.args.redefineSignalPOIs.split(',')
    else:
      poiList = utils.list_from_workspace(ws, 'w', 'ModelConfig_POI')
    #print 'Have nuisance parameters: ' + str(paramList)
    print 'Have POIs: ' + str(poiList)
    poistr = ','.join(poiList)
    if self.args.doInitialFit:
      if self.args.splitInitial:
        for poi in poiList:
          self.job_queue.append('combine -M MultiDimFit -n _initialFit_%(name)s_POI_%(poi)s --algo singles --redefineSignalPOIs %(poistr)s --floatOtherPOIs 1 --saveInactivePOI 1 -P %(poi)s %(pass_str)s --altCommit' % vars())
      else:
        self.job_queue.append('combine -M MultiDimFit -n _initialFit_%(name)s --algo singles --redefineSignalPOIs %(poistr)s %(pass_str)s --altCommit' % vars())
      self.flush_queue()
      sys.exit(0)
    initialRes = utils.get_singles_results('higgsCombine_initialFit_%(name)s.MultiDimFit.mH%(mh)s.root' % vars(), poiList, poiList)
    if len(named) > 0:
      paramList = named
    else:
      paramList = utils.list_from_workspace(ws, 'w', 'ModelConfig_NuisParams')
    print 'Have nuisance parameters: ' + str(len(paramList))
    prefit = utils.prefit_from_workspace(ws, 'w', paramList)
    res = { }
    res["POIs"] = []
    res["params"] = []
    for poi in poiList:
      res["POIs"].append({"name" : poi, "fit" : initialRes[poi][poi]})

    missing = [ ]
    for param in paramList:
      pres = { }
      # print 'Doing param ' + str(counter) + ': ' + param
      if self.args.doFits:
        self.job_queue.append('combine -M MultiDimFit -n _paramFit_%(name)s_%(param)s --algo singles --redefineSignalPOIs %(param)s,%(poistr)s -P %(param)s --floatOtherPOIs 1 --saveInactivePOI 1 %(pass_str)s --altCommit' % vars())
      else:
        paramScanRes = utils.get_singles_results('higgsCombine_paramFit_%(name)s_%(param)s.MultiDimFit.mH%(mh)s.root' % vars(), [param], poiList + [param])
        if paramScanRes is None:
          missing.append(param)
          continue
        pres.update({"name" : param, "fit" : paramScanRes[param][param], "prefit" : prefit[param]})
        for p in poiList:
          pres.update({p : paramScanRes[param][p], 'impact_'+p : (paramScanRes[param][p][2] - paramScanRes[param][p][0])/2.})
        res['params'].append(pres)
    self.flush_queue()
    jsondata = json.dumps(res, sort_keys=True, indent=2, separators=(',', ': '))
    print jsondata
    if self.args.output is not None:
      with open(self.args.output, 'w') as out_file:
        out_file.write(jsondata)
    if len(missing) > 0:
      print 'Missing inputs: ' + ','.join(missing)

