#!/usr/bin/env python

import ROOT
import json
import os

import CombineHarvester.CombineTools.combine.utils as utils
from CombineHarvester.CombineTools.combine.opts import OPTS

from CombineHarvester.CombineTools.combine.CombineToolBase import CombineToolBase


class PrintFit(CombineToolBase):
    description = 'Print the output of MultimDitFit'
    requires_root = True

    def __init__(self):
        CombineToolBase.__init__(self)

    def attach_args(self, group):
        CombineToolBase.attach_args(self, group)
        group.add_argument('input', help='The input file')
        group.add_argument(
            '--algo', help='The algo used in MultiDimFit', default='none')
        group.add_argument(
            '-P', '--POIs', help='The params that were scanned (in scan order)')
        group.add_argument(
            '--json', help='Write json output (format file.json:key1:key2..')

    def run_method(self):
        if self.args.json is not None:
            json_structure = self.args.json.split(':')
            assert(len(json_structure) >= 1)
            if os.path.isfile(json_structure[0]):
                with open(json_structure[0]) as jsonfile: js = json.load(jsonfile)
            else:
                js = {}
            js_target = js
            if (len(json_structure) >= 2):
                for key in json_structure[1:]:
                    js_target[key] = {}
                    js_target = js_target[key]
        POIs = self.args.POIs.split(',')
        if self.args.algo == 'none':
            res = utils.get_none_results(self.args.input, POIs)
            if self.args.json is not None:
              for key,val in res.iteritems():
                js_target[key] = { 'Val' : val }
            with open(json_structure[0], 'w') as outfile:
              json.dump(js, outfile, sort_keys=True, indent=4, separators=(',', ': '))
        elif self.args.algo == 'singles':
            res = utils.get_singles_results(self.args.input, POIs, POIs)
            for p in POIs:
                val = res[p][p]
                print '%s = %.3f -%.3f/+%.3f' % (p, val[1], val[1] - val[0], val[2] - val[1])


class CollectLimits(CombineToolBase):
    description = 'Aggregate limit output from combine'
    requires_root = True

    def __init__(self):
        CombineToolBase.__init__(self)

    def attach_args(self, group):
        CombineToolBase.attach_args(self, group)
        group.add_argument(
            '-i', '--input', nargs='+', default=[], help='The input files')
        group.add_argument(
            '-o', '--output', help='The name of the output json file')

    def run_method(self):
        js_out = {}
        for filename in self.args.input:
            file = ROOT.TFile(filename)
            if file.IsZombie():
                continue
            tree = file.Get('limit')
            for evt in tree:
                mh = str(evt.mh)
                if mh not in js_out:
                    js_out[mh] = {}
                if evt.quantileExpected == -1:
                    js_out[mh]['observed'] = evt.limit
                elif abs(evt.quantileExpected - 0.5) < 1E-4:
                    js_out[mh]["expected"] = evt.limit
                elif abs(evt.quantileExpected - 0.025) < 1E-4:
                    js_out[mh]["-2"] = evt.limit
                elif abs(evt.quantileExpected - 0.160) < 1E-4:
                    js_out[mh]["-1"] = evt.limit
                elif abs(evt.quantileExpected - 0.840) < 1E-4:
                    js_out[mh]["+1"] = evt.limit
                elif abs(evt.quantileExpected - 0.975) < 1E-4:
                    js_out[mh]["+2"] = evt.limit
        # print js_out
        jsondata = json.dumps(
            js_out, sort_keys=True, indent=2, separators=(',', ': '))
        print jsondata
        if self.args.output is not None:
            with open(self.args.output, 'w') as out_file:
                out_file.write(jsondata)
