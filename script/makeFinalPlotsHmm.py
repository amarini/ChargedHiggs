import os,sys
from array import array
import re
from optparse import OptionParser, OptionGroup

parser=OptionParser()
parser.add_option("-i","--input",type='string',help="Input ROOT file. [%default]", default="Hmumu.root")
parser.add_option("-d","--dir",dest='dir',type="string",help="directory [%default]",default="Vars")
parser.add_option("-v","--var",dest='var',type="string",help="variable [%default]",default="Mmm")
parser.add_option("-o","--outdir",dest='outdir',type="string",help="output directory [%default]",default="Hmumu")

print "-> Looking for basepath"
basepath = ""
mypath = os.path.abspath(os.getcwd())
while mypath != "" and mypath != "/":
	if "ChargedHiggs" in os.path.basename(mypath):
		basepath = os.path.abspath(mypath)
	mypath = os.path.dirname(mypath)
print "-> Base Path is " + basepath
sys.path.insert(0,basepath)
sys.path.insert(0,basepath +"/python")
from hmm import hmm

#extra = OptionGroup(parser,"Extra options:","")
#extra.add_option("-r","--rebin",type='int',help = "Rebin Histograms. if >1000 variable bin [%default]", default=1)
opts,args= parser.parse_args()

########### IMPORT ROOT #############
sys.argv=[]
import ROOT

ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)
if opts.outdir != "":
	ROOT.gROOT.SetBatch()


############# definitions
categories=hmm.categories
##for m in [ "BB","BO","BE","OO","OE","EE" ]:
##   for v in ["VBF0","OneB","GF","VBF1","Untag0","Untag1"]:
##      categories.append(v + "_" + m )

#sigMonteCarlos= ["VBF_HToMuMu_M%d","GluGlu_HToMuMu_M%d","ZH_HToMuMu_M%d","WMinusH_HToMuMu_M%d","WPlusH_HToMuMu_M%d","ttH_HToMuMu_M%d"]
sigMonteCarlos = []
for proc in hmm.processes:
	sigMonteCarlos .append( proc+"_HToMuMu_M%d" )

## 125 first
masses = [125,120,130]

###############################

def MpvAndSigmaEff(h, q=0.68):
    ''' Return mpv and sigma eff'''
    imax=-1
    valmax=0.0
    for ibin in range(0,h.GetNbinsX()):
        if h.GetBinContent(ibin+1) > valmax:
            valmax=h.GetBinContent(ibin+1) 
            imax= ibin+1
    s=h.Integral()

    low=h.GetBinCenter(1)
    high=h.GetBinCenter(h.GetNbinsX())

    for ibin in range(0,h.GetNbinsX()):
        for jbin in range(ibin+1,h.GetNbinsX()):
            if h.Integral(ibin+1,jbin+1)> q *s:
                if h.GetBinCenter(jbin+1)-h.GetBinCenter(ibin+1) < high -low:
                    low = h.GetBinCenter(ibin+1)
                    high=h.GetBinCenter(jbin+1)
                #break ## j -loop can end here
    return (h.GetBinCenter(imax), low, high )

def SoB(h,hdata,low,high,type=""):
	## xsec at 125
	## these numbers are in pb
	br=hmm.br();
	#br = 2.176E-04
	xsec=hmm.xsec(type)
	lumi = hmm.lumi()

	hdata_ = hdata.Clone(hdata.GetName()+"_fit")
	s= h.Integral(h.FindBin(low),h.FindBin(high))
	#f=ROOT.TF1("myfunc","[0]*TMath::Exp(-x*[1])",115,122)
	f=ROOT.TF1("myfunc","[0]*TMath::Exp(-x*[1])",115,122)
	f.SetParameter(0,hdata.Integral( hdata.FindBin(115),hdata.FindBin(122)))
	hdata.Fit("myfunc","QRN")
	hdata.Fit("myfunc","QRMN")
	## fill an histogram to be sure that border conditions are well met
	for ibin in range(0,hdata_.GetNbinsX()):
		if hdata_.GetBinContent(ibin+1)<=0:
			hdata_.SetBinContent( ibin+1,f.Eval(hdata_.GetBinCenter(ibin+1)) ) 
	b= hdata_.Integral(h.FindBin(low),h.FindBin(high))
	if opts.outdir=="":
		c2=ROOT.TCanvas("c2","c2",800,800)
		hdata.Draw("PE")
		f.Draw("L SAME")
		raw_input("fit to data")
	#b= f.Integral(mean-low,mean+high)
	return (s*br*lumi*xsec,b)


## get files
fIn = ROOT.TFile.Open(opts.input,"READ")
if fIn == None: 
	   print "<*> NO File '%s'"%opts.input
	   raise IOError

canvases=[]
garbage=[]

doSig=False
if doSig:
  for cat in categories:
    for mc in sigMonteCarlos:
        c=ROOT.TCanvas("c_"+cat+"_"+mc,"canvas",800,800)
        c.SetTopMargin(0.05)
        c.SetRightMargin(0.05)
        c.SetBottomMargin(0.15)
        c.SetLeftMargin(0.15)
        mpv=0
        seff=0.0
        ea=0.0
	sob=0.0
        hdata=fIn.Get("HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_Data" )
	if hdata==None:
		print "<!> Ignoring", "HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_Data"
		continue
        for idx,m in enumerate(masses):
            h=fIn.Get("HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_"+mc%(m) )
	    if h==None:
		    print "<*> Ignoring", "HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_"+mc%(m) 
		    continue
            garbage.append(h)
            h.SetLineColor(ROOT.kBlack)
            h.SetLineWidth(2)
            if idx==0:
		c.cd()
                h.Draw("AXIS")
                h.Draw("AXIS X+ Y+ SAME")
                h.GetXaxis().SetTitle("m^{#mu#mu}[GeV]")
                h.GetXaxis().SetTitleOffset(1.2)
                h.GetYaxis().SetTitle("#varepsilon A")
                h.GetYaxis().SetTitleOffset(1.2)
                h.GetXaxis().SetRangeUser(100,150)
		#color=38
		color=46
                h.SetLineColor(color)
                h.SetLineWidth(2)
                h.SetFillColor(color)
                h.SetFillStyle(3004)
                ea = h.Integral()
                mpv, low ,high =  MpvAndSigmaEff(h, 0.682689)
                seff = (high - low)/2.0

		if hdata !=None:
			s,b=SoB(h,hdata,low,high,re.sub("_HToMuMu.*","",mc))
			c.cd()
		else : 
			s,b = (0,0)

		try:
			sob=s/b
		except ZeroDivisionError:
			sob=-1

                l1 = ROOT.TLine(low,0,low,h.GetMaximum()*0.8)
                l2 = ROOT.TLine(high,0,high,h.GetMaximum()*0.8)
                l1.SetLineWidth(2)
                l2.SetLineWidth(2)
                l1.SetLineColor(ROOT.kGray)
                l2.SetLineColor(ROOT.kGray)
                l1.Draw("L SAME")
                l2.Draw("L SAME")
                garbage.extend([l1,l2])
            h.Draw("HIST SAME")
        txt=ROOT.TLatex()
        txt.SetNDC()
        txt.SetTextFont(43)
        txt.SetTextSize(20)
        txt.SetTextAlign(31)
        txt.DrawLatex(.95,.96,"%.1f fb^{-1} (13 TeV)"%(float(hmm.lumi()/1000.)))
        txt.SetTextSize(30)
        txt.SetTextAlign(13)
        txt.DrawLatex(.16,.93,"#bf{CMS} #scale[0.7]{#it{Preliminary}}")
        txt.SetTextSize(20)
        txt.SetTextAlign(11)
        d=0.04
        txt.DrawLatex(.73,.90 - 0*d,"#bf{Cat="+cat+"}")
        txt.DrawLatex(.73,.90 - 1*d,"Proc="+re.sub("_HToMuMu.*","",mc))
        txt.DrawLatex(.73,.90 - 2*d,"mpv=%.1f GeV"%mpv)
        txt.DrawLatex(.73,.90 - 3*d,"seff=%.1f GeV"%seff)
        txt.DrawLatex(.73,.90 - 4*d,"#varepsilon A=%.1f %%"%(ea*100))
        txt.DrawLatex(.73,.90 - 5*d,"S/B = %.1f %%"%(sob*100))
	c.Modify()
	c.Update()
	if opts.outdir=="":
		raw_input("ok?")
	else:
		c.SaveAs(opts.outdir + "/" + cat + "_" + re.sub("_HToMuMu.*","",mc) + ".pdf")
		c.SaveAs(opts.outdir + "/" + cat + "_" + re.sub("_HToMuMu.*","",mc) + ".png")

## DATA / MC PLOTS
tmp=ROOT.TFile("/tmp/"+os.environ['USER']+"/tmp.root","RECREATE")
tmp.cd()

rebin=10
doBkg=True
if doBkg:
   for cat in categories: 
   #HmumuAnalysis/Vars/Mmm_VBF0_BE_ttH_HToMuMu_M125
   #for cat in ["VBF0_BE"]:
        c=ROOT.TCanvas("c_"+cat+"_bkg","canvas",800,1000)
	pup=ROOT.TPad("up_"+cat,"up",0,.2,1,1)
	pdown=ROOT.TPad("down_"+cat,"up",0,0,1,.2)

        pup.SetTopMargin(0.05)
        pup.SetRightMargin(0.05)
        pup.SetBottomMargin(0)
        pup.SetLeftMargin(0.15)

        pdown.SetTopMargin(0.0)
        pdown.SetRightMargin(0.05)
        pdown.SetBottomMargin(0.50)
        pdown.SetLeftMargin(0.15)

	pup.Draw()
	pdown.Draw()

	leg = ROOT.TLegend(.68,.65,.92,.85)
	leg.SetFillStyle(0)
	leg.SetBorderSize(0)
	## column in the right order
	leg1=[]
	leg2=[]

	tmp.cd()
	print "-> Getting data hist","HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_Data"
        hdata=fIn.Get("HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_Data" )
	hdata.Rebin(rebin)
	hdata.SetMarkerStyle(20)
	hdata.SetMarkerColor(ROOT.kBlack)
	hdata.SetLineColor(ROOT.kBlack)
	leg.AddEntry(hdata,"Data","PE")
	#mcs=["DY","TT","ST","WZ","WW","ZZ"]
	BkgMonteCarlos=["ZZ","WW","WZ","ST","TT","DY"]
	mcAll=None

	bkg=ROOT.THStack()
	bkg.SetName("bkgmc_"+cat)

	sig=ROOT.THStack()
	sig.SetName("sigmc_"+cat)

        garbage.extend([sig,bkg,leg])

	## BLIND 120-130
	blind=True
	if blind:
		ibin0= hdata.FindBin(120)
		ibin1= hdata.FindBin(130)
		for ibin in range(ibin0,ibin1+1):
			hdata.SetBinContent(ibin,0)
			hdata.SetBinError(ibin,0)

	for mc in BkgMonteCarlos:
            print "* Getting bkg","HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_"+mc
            h=fIn.Get("HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_"+mc )
	    if h==None:
		    print "<*> Ignoring", "HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_"+mc
		    continue
            garbage.append(h)
	    h.Rebin(rebin)
	    h.Scale(hmm.lumi())
            h.SetLineColor(ROOT.kBlack)
            h.SetLineWidth(2)
	    if mc == 'DY':
		    h.SetFillColor(ROOT.kBlue-10)
		    leg1.append( (h,"DY","F") )
		    #leg.AddEntry(h,"DY","F")
	    elif mc == 'TT':
		    h.SetFillColor(ROOT.kRed-10)
		    leg1.append( (h,"t#bar{t}+st","F"))
		    #leg.AddEntry(h,"t#bar{t}+st","F")
	    elif mc == 'ST':
                    h.SetLineWidth(0)
		    h.SetLineColor(ROOT.kRed-10)
		    h.SetFillColor(ROOT.kRed-10)
	    elif mc == 'WW' or mc == "ZZ":
                    h.SetLineWidth(0)
		    h.SetLineColor(ROOT.kGreen-10)
		    h.SetFillColor(ROOT.kGreen-10)
	    elif mc == 'WZ' :
		    h.SetFillColor(ROOT.kGreen-10)
		    #leg.AddEntry(h,"VV","F")
		    leg1.append((h,"VV","F"))

	    bkg.Add(h)

	    if mcAll==None:
		    mcAll=h.Clone("mcAll_"+cat)
	    else:
		    mcAll.Add(h)


	for mc in reversed(sigMonteCarlos):
	    m=125
	    print "* Getting sig","HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_"+mc%(m) 
	    try:
               h=fIn.Get("HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_"+mc%(m) )
	    except:
	        h=None
	    if h==None: 
		    print "<*> Ignoring", "HmumuAnalysis/"+opts.dir+"/" + opts.var + "_" + cat +"_"+mc%(m)
		    continue

            garbage.append(h)
	    h.Rebin(rebin)
	    h.Scale(hmm.lumi())
	    ##for ibin in range(0,h.GetNbinsX()):
	    ##    if h.GetBinContent(ibin)<0: 
	    ##        h.SetBinContent(ibin,0.0) ## otherwise stack fails
	    ## xsec x br
	    br = hmm.br()
            h.SetLineColor(ROOT.kBlack)
            h.SetLineWidth(3)
            h.SetFillStyle(0)
	    if 'GluGlu' in mc:
		    h.SetLineColor(38)
		    xsec=hmm.xsec("ggH")
		    #leg.AddEntry(h,"ggH","L")
		    leg2.append((h,"ggH","L"))
	    elif 'VBF' in mc:
		    h.SetLineColor(46)
		    h.SetLineStyle(2)
		    #leg.AddEntry(h,"qqH","L")
		    leg2.append((h,"qqH","L"))
		    xsec=hmm.xsec("VBF")
	    elif 'WMinusH' in mc: 
		    h.SetLineColor(ROOT.kGreen+2)
		    h.SetLineStyle(2)
		    xsec=hmm.xsec("WPlusH")
		    #leg.AddEntry(h,"W^{+}H","L")
		    leg2.append((h,"W^{+}H","L"))
	    elif 'WPlusH' in mc:
		    h.SetLineColor(ROOT.kGreen+2)
		    h.SetLineStyle(7)
		    xsec=hmm.xsec("WMinusH")
		    #leg.AddEntry(h,"W^{-}H","L")
		    leg2.append((h,"W^{-}H","L"))
	    elif 'ZH' in mc:
		    h.SetLineColor(ROOT.kCyan)
		    h.SetLineStyle(3)
		    #leg.AddEntry(h,"ZH","L")
		    leg2.append((h,"ZH","L"))
		    xsec=hmm.xsec("ZH")
	    elif 'ttH' in mc:
		    h.SetLineColor(ROOT.kOrange)
		    h.SetLineStyle(3)
		    #leg.AddEntry(h,"ttH","L")
		    leg2.append((h,"ttH","L"))
		    xsec=hmm.xsec("ttH")

	    h.Scale(xsec*br)
	    sig.Add(h)

	c.cd()
	pup.cd()
        bkg.Draw("HIST")
        bkg.Draw("AXIS X+ Y+ SAME")
        bkg.GetXaxis().SetTitle("m^{#mu#mu}[GeV]")
        bkg.GetXaxis().SetTitleOffset(2.0)
        bkg.GetYaxis().SetTitle("Events")
        bkg.GetYaxis().SetTitleOffset(2.0)
        bkg.GetXaxis().SetRangeUser(60,150)

        bkg.GetYaxis().SetLabelFont(43)
        bkg.GetXaxis().SetLabelFont(43)
        bkg.GetYaxis().SetTitleFont(43)
        bkg.GetXaxis().SetTitleFont(43)
        bkg.GetYaxis().SetLabelSize(20)
        bkg.GetXaxis().SetLabelSize(20)
        bkg.GetYaxis().SetTitleSize(24)
        bkg.GetXaxis().SetTitleSize(24)
	#color=38
	sig.Draw("HIST SAME")
    	hdata.Draw("P E X0 SAME")

        txt=ROOT.TLatex()
        txt.SetNDC()
        txt.SetTextFont(43)
        txt.SetTextSize(20)
        txt.SetTextAlign(31)
        txt.DrawLatex(.95,.96,"%.1f fb^{-1} (13 TeV)"%(float(hmm.lumi()/1000.)))
        txt.SetTextSize(30)
        txt.SetTextAlign(13)
        txt.DrawLatex(.16,.93,"#bf{CMS} #scale[0.7]{#it{Preliminary}}")
        txt.SetTextSize(20)
        txt.SetTextAlign(11)
        txt.DrawLatex(.73,.90,"#bf{Cat="+cat+"}")

	leg.SetNColumns(2)

	#leg1.reverse()
	#leg2.reverse()
	while True:
		if len(leg2) !=0:
			h,label,opt = leg2.pop()
			leg.AddEntry(h,label,opt)
		if len(leg1) !=0:
			h,label,opt = leg1.pop()
			leg.AddEntry(h,label,opt)
		if len(leg1) ==0 and len(leg2)==0:
			break

	leg.Draw("SAME")

	pup.SetLogy()

	c.Modify()
	c.Update()

	pdown.cd()
	r=hdata.Clone("r")
	for ibin in range(0,mcAll.GetNbinsX()):
		mcAll.SetBinError(ibin,0)
	r.Divide(mcAll)

        r.Draw("AXIS")
        r.Draw("AXIS X+ Y+ SAME")
        r.GetXaxis().SetTitle("m^{#mu#mu}[GeV]")
        r.GetXaxis().SetTitleOffset(1.2)
        r.GetYaxis().SetTitle("Events")
        r.GetYaxis().SetTitleOffset(2.0)
        r.GetXaxis().SetTitleOffset(5.0)
        r.GetXaxis().SetRangeUser(60,150)
        r.GetYaxis().SetRangeUser(0.5,1.5)
        r.GetYaxis().SetLabelFont(43)
        r.GetXaxis().SetLabelFont(43)
        r.GetYaxis().SetTitleFont(43)
        r.GetXaxis().SetTitleFont(43)
        r.GetYaxis().SetLabelSize(20)
        r.GetXaxis().SetLabelSize(20)
        r.GetYaxis().SetTitleSize(24)
        r.GetXaxis().SetTitleSize(24)
        r.GetYaxis().SetNdivisions(502)

	g=ROOT.TGraph()
	g.SetName("1_"+cat)
	g.SetPoint(0,60,1)
	g.SetPoint(1,150,1)
	g.SetLineColor(ROOT.kGray+2)
	g.SetLineStyle(7)
	g.SetLineWidth(2)

        g.Draw("L SAME")

        r.Draw("P E X0 SAME")

	garbage.extend([g,r])

	if opts.outdir=="":
		raw_input("ok?")
	else:
		c.SaveAs(opts.outdir + "/" + cat + "_bkg" + ".pdf")
		c.SaveAs(opts.outdir + "/" + cat + "_bkg" + ".png")
	#try to clean
	for g in garbage:
		g.Delete()
	garbage=[]

	fIn.Close()
	fIn = ROOT.TFile.Open(opts.input,"READ")
	if fIn == None: 
	    print "<*> NO File '%s'"%opts.input
	    raise IOError
	
#Local Variables:
#mode:python
#indent-tabs-mode:nil
#tab-width:4
#c-basic-offset:4
#End:
#vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 
