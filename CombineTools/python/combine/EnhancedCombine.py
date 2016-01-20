import itertools
import CombineHarvester.CombineTools.combine.utils as utils
import json
#import os
from CombineHarvester.CombineTools.combine.opts import OPTS

from CombineHarvester.CombineTools.combine.CombineToolBase import CombineToolBase


class EnhancedCombine(CombineToolBase):
    description = 'combine pass-through with special treatment for some options [DEFAULT]'
    requires_root = False

    def __init__(self):
        CombineToolBase.__init__(self)

    def attach_intercept_args(self, group):
        CombineToolBase.attach_intercept_args(self, group)
        group.add_argument(
            '-m', '--mass', help='Supports range strings for multiple masses, e.g. "120:130:5,140 will produce three combine calls with mass values of 120, 125, 130 and 140"')
        group.add_argument(
            '--points', help='For use with "-M MultiDimFit --algo grid" to split scan points into separate jobs')
        group.add_argument(
            '--singlePoint', help='Supports range strings for multiple points to test, uses the same format as the --mass argument')
        group.add_argument(
            '--boundlist', help='Name of json-file which contains the ranges of physical parameters depending on the given mass and given physics model')
        group.add_argument('--name', '-n', default='.Test',
                           help='Name used to label the combine output file, can be modified by other options')

    def attach_args(self, group):
        CombineToolBase.attach_args(self, group)
        group.add_argument(
            '--opts', nargs='+', default=[], help='Add preset combine option groups')
        group.add_argument('--split-points', type=int, default=0,
                           help='When used in conjunction with --points will create multiple combine calls that each run at most the number of points specified here.')

    def set_args(self, known, unknown):
        CombineToolBase.set_args(self, known, unknown)
        if hasattr(self.args, 'opts'):
            for opt in self.args.opts:
                self.passthru.append(OPTS[opt])

    def run_method(self):
        # Put the method back in because we always take it out
        self.put_back_arg('method', '-M')

        cmd_queue = []
        subbed_vars = {}

        if self.args.mass is not None:
            mass_vals = utils.split_vals(self.args.mass)
            subbed_vars[('MASS',)] = [(mval,) for mval in mass_vals]
            self.passthru.extend(['-m', '%(MASS)s'])

        if self.args.singlePoint is not None:
            single_points = utils.split_vals(self.args.singlePoint)
            subbed_vars[('SINGLEPOINT',)] = [(pval,) for pval in single_points]
            self.passthru.extend(['--singlePoint', '%(SINGLEPOINT)s'])
            self.args.name += '.POINT.%(SINGLEPOINT)s'

        if self.args.boundlist is not None:
          subbed_vars = {}
          with open(self.args.boundlist) as json_file:
            bnd = json.load(json_file)
          command1=['' for i in mass_vals]
          #command2=['' for i in mass_vals]
          i=0
          for mval in mass_vals:
            for model in bnd:
              if not (command1[i]==''): command1[i]=command1[i]+':'
              #if not (command2[i]==''): command2[i]=command2[i]+','
              command1[i]=command1[i]+model+'=0,'+str(bnd[model][mval])
            #  command2[i]=command2[i]+model+'=0' #'='+str(float(bnd[model][mval])/2.0)
            i+=1
          #subbed_vars[('MASS', 'MODELBOUNDONE', 'MODELBOUNDTWO')] = [(mass_vals[i], command1[i], command2[i]) for i in range(len(mass_vals))]
          subbed_vars[('MASS', 'MODELBOUNDONE')] = [(mass_vals[i], command1[i]) for i in range(len(mass_vals))]
          self.passthru.extend(['--setPhysicsModelParameterRanges',  '%(MODELBOUNDONE)s'])
          #self.passthru.extend(['--setPhysicsModelParameters',  '%(MODELBOUNDTWO)s'])

        if self.args.points is not None:
            self.passthru.extend(['--points', self.args.points])
        if (self.args.split_points is not None and
                self.args.split_points > 0 and
                self.args.points is not None):
            points = int(self.args.points)
            split = self.args.split_points
            start = 0
            ranges = []
            while (start + (split - 1)) <= points:
            #    filename = "higgsCombine"+self.args.name+".POINTS."+str(start)+"."+str(start+(split-1))+".MultiDimFit.mH"+str(self.args.mass)+".root"
            #    if (not os.path.isfile(filename)) or (os.path.getsize(filename)<1024):
            #        # Send job, if the file it's supposed to create doesn't exist yet
            #        # or if the file is empty because the previous job didn't finish
                ranges.append((start, start + (split - 1)))
                start += split
            if start < points:
            #    filename = "higgsCombine"+self.args.name+".POINTS."+str(start)+"."+str(points - 1)+".MultiDimFit.mH"+str(self.args.mass)+".root"
            #    if (not os.path.isfile(filename)) or (os.path.getsize(filename)<1024):
                ranges.append((start, points - 1))
            #if (ranges == []):
            #    print "No jobs were created; All files already exist"
            #    exit()
            subbed_vars[('P_START', 'P_END')] = [(r[0], r[1]) for r in ranges]
            self.passthru.extend(
                ['--firstPoint %(P_START)s --lastPoint %(P_END)s'])
            self.args.name += '.POINTS.%(P_START)s.%(P_END)s'

        # can only put the name option back now because we might have modified
        # it from what the user specified
        self.put_back_arg('name', '-n')
        proto = 'combine ' + (' '.join(self.passthru))
        for it in itertools.product(*subbed_vars.values()):
            keys = subbed_vars.keys()
            dict = {}
            for i, k in enumerate(keys):
                for tuple_i, tuple_ele in enumerate(k):
                    dict[tuple_ele] = it[i][tuple_i]
            self.job_queue.append(proto % dict)
        self.flush_queue()
