import ROOT
import array
from ROOT import gPad


masses1 = [80, 90, 100, 110, 120, 130, 140, 160, 180, 600, 900, 1000, 1200, 1500, 2900, 3200]
ROOT.gROOT.SetBatch(True)


def plotLimits( signal, channel ) :

    masses = masses1

    limits = [[0 for x in range( len(masses) )] for x in range(5)]
    print limits

    mCnt = 0
    for mass in masses :
        if channel != 'll' :
            f = ROOT.TFile('LIMITS/%s/%s/higgsCombineTest.Asymptotic.mH%i.root' % ( signal, channel, mass), 'r')
        else :
            f = ROOT.TFile('%s/higgsCombineLL.Asymptotic.mH%i.root' % (signal,  mass), 'r')
        t = f.Get('limit')
        print "Channel: ",channel,"   Mass: ",mass
        i = 0
        for row in t :
            if row.quantileExpected == -1 : continue
            #print "Sig: ",row.quantileExpected," limit: ",row.limit
            limits[i][mCnt] = row.limit
            #limits[i].append( row.limit )
            i += 1
            
        mCnt += 1


    n = len(masses)
    neg2 = ROOT.TGraph( len(masses))
    neg1 = ROOT.TGraph( len(masses))
    med = ROOT.TGraph( len(masses))
    pos1 = ROOT.TGraph( len(masses))
    pos2 = ROOT.TGraph( len(masses))
    midShade = ROOT.TGraph( len(masses)*2)
    outShade = ROOT.TGraph( len(masses)*2)
    for i in range( len(masses) ) :
        neg2.SetPoint( i, masses[i], limits[0][i] )
        neg1.SetPoint( i, masses[i], limits[1][i] )
        med.SetPoint( i, masses[i], limits[2][i] )
        pos1.SetPoint( i, masses[i], limits[3][i] )
        pos2.SetPoint( i, masses[i], limits[4][i] )
        midShade.SetPoint( i, masses[i],limits[3][i] )
        midShade.SetPoint( n+i, masses[n-i-1],limits[1][n-i-1] )
        outShade.SetPoint( i, masses[i],limits[4][i] )
        outShade.SetPoint( n+i, masses[n-i-1],limits[0][n-i-1] )


    outShade.SetFillStyle(1001)
    outShade.SetFillColor(5)
    midShade.SetFillStyle(1001)
    midShade.SetFillColor(3)
    c2 = ROOT.TCanvas( 'c2', 'c2', 600, 600 )
    p1 = ROOT.TPad( 'p1', 'p1', 0, 0, 1, 1)
    p1.Draw()
    p1.cd()
    med.SetLineStyle(2)
    outShade.GetXaxis().SetTitle('Visible Mass (GeV)')
    outShade.GetXaxis().SetTitleOffset( outShade.GetXaxis().GetTitleOffset() * 1.3 )
    if signal=="bbH":
       outShade.GetYaxis().SetTitle('95% CL limit on #sigma(bb#phi) x BR(#phi#rightarrow #tau#tau) [pb]')
    else:
       outShade.GetYaxis().SetTitle('95% CL limit on #sigma(gg#phi) x BR(#phi#rightarrow #tau#tau) [pb]')
    outShade.GetYaxis().SetTitleOffset( outShade.GetYaxis().GetTitleOffset() * 1.3 )
    outShade.SetTitle('Expected Limits A/H #rightarrow #tau#tau: Channel %s' % channel)
    
    outShade.Draw('Af')
    midShade.Draw('f')
    med.Draw('l')
    p1.SetLogy()
    p1.SetLogx()
    
    c2.SaveAs('Limits_%s_%s.png' % (signal, channel) )


channels = ['mt', 'et']
signals = ['ggH','bbH']
for signal in signals :
    for channel in channels :
        plotLimits( signal, channel )
