#!/usr/bin/env python3

"""Plot validation results."""

# %% Imports
import os,glob
import pyslha,imp
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from getContour import getContour
from scipy.interpolate import griddata

pd.options.mode.chained_assignment = None #Disable copy warnings
#Define plotting style:
sns.set() #Set style
sns.set_style('ticks',{'font.family':'serif', 'font.serif':'Times New Roman'})
sns.set_context('paper', font_scale=1.8)
cm = plt.cm.get_cmap('RdYlBu')

# %% Load data
#Official curve
excATLAS = np.genfromtxt('./HEPData-ins1641262-v4-Exclusion_contour_EW_2_obs_conv.txt',
                       names=True)

# %% Get data from CheckMate results
resultFolder = '../data/TDTM1M2F_cm'
smodelsFolder = '../data/TDTM1M2F_smodels'
slhaFolder = '../data/TDTM1M2F_slha'
rDataCM = []
rDataSMS = []
for slhaFile in glob.glob(slhaFolder+'/*.slha'):
    slhaData = pyslha.readSLHAFile(slhaFile)
    mC1 = slhaData.blocks['MASS'][1000024]
    widthC1 = slhaData.decays[1000024].totalwidth
    ctau_ns = 6.582e-16/widthC1
    xsecC1C1 = [x for x in slhaData.xsections[(2212,2212,-1000024,1000024)].xsecs if x.sqrts == 13000.][0].value
    xsecC1pN1 = [x for x in slhaData.xsections[(2212,2212,1000022,1000024)].xsecs if x.sqrts == 13000.][0].value
    xsecC1mN1 = [x for x in slhaData.xsections[(2212,2212,-1000024,1000022)].xsecs if x.sqrts == 13000.][0].value
    xsectot_fb = (xsecC1C1+xsecC1pN1+xsecC1mN1)*1e3
    resDir = os.path.splitext(os.path.basename(slhaFile))[0]
    resFile = os.path.join(resultFolder,resDir,'evaluation',
                'total_results.txt')
    if not os.path.isfile(resFile):
        # print('skipping',slhaFile)
        continue
    data = np.genfromtxt(resFile,names=True,dtype=None,encoding=None)
    basename =os.path.basename(slhaFile)
    resFile = os.path.join(smodelsFolder,basename+'.py')
    if not os.path.isfile(resFile):
        # print('skipping',slhaFile)
        continue
    smodelsDict = imp.load_source(resFile.replace('.py',''),resFile).smodelsOutput

    #Get checkmate data
    data = data[data['sr'] == 'SR1'] #Select (unique) signal region
    ns = data['s'][0]
    ds = data['ds'][0]
    eff = data['eff'][0]
    if eff:
        sigUL = 0.22/eff
    else:
        sigUL = -1.0
    if ns > 0:
        ds_rel = ds/ns
    else:
        ds_rel = ds/1.0
    rDataCM.append([mC1,ctau_ns,data['robs'][0],data['robscons'][0],ds_rel,sigUL,eff])

    #Get smodels data
    if not 'ExptRes' in smodelsDict:
        eff = 0
        r = 0
    else:
        tp_fb = smodelsDict['ExptRes'][0]['theory prediction (fb)']
        r = smodelsDict['ExptRes'][0]['r']
        eff = tp_fb/xsectot_fb
    if eff:
        sigUL = 0.22/eff
    else:
        sigUL = -1.0
    rDataSMS.append([mC1,ctau_ns,r,sigUL,eff])

rDataCM = np.array(rDataCM)
rDataSMS = np.array(rDataSMS)


## %% Get exclusion contours for signal
contoursCM = getContour(rDataCM[:,0],rDataCM[:,1],rDataCM[:,2],levels=[0.83,0.9,1.0],ylog=True)
contoursSMS = getContour(rDataSMS[:,0],rDataSMS[:,1],rDataSMS[:,2],levels=[0.83,0.9,1.0],ylog=True)

## %% Compute relative difference
effDiff = np.zeros(rDataCM[:,-1].shape)
effDiff = np.divide(2*(rDataCM[:,-1]-rDataSMS[:,-1]),(rDataCM[:,-1]+rDataSMS[:,-1]),
                where= ((rDataCM[:,-1] > 0) & (rDataSMS[:,-1] > 0)),out=effDiff)
effRatio = np.ones(rDataCM[:,-1].shape)
effRatio = np.divide(rDataSMS[:,-1],rDataCM[:,-1],
                where= rDataCM[:,-1] > 0,out=effRatio)



# %% plot results
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(10,6))
# ax = axes.scatter(rDataCM[:,0],rDataCM[:,1],
    # c=rDataSMS[:,-1]/rDataCM[:,-1],cmap=cm,vmin=0.5,vmax=1.5,s=120)

cmap = plt.get_cmap('RdYlBu', 11)
_,_,_,ax = axes.hist2d(rDataCM[:,0],rDataCM[:,1],weights=rDataSMS[:,-1]/rDataCM[:,-1],
                bins=[sorted(rDataCM[:,0]),sorted(rDataCM[:,1])],cmap=cmap,vmin=0.5,vmax=1.5)

axes.plot(excATLAS['mC1_GeV'], 6.582e-16/excATLAS['width_GeV'],linestyle='-',c='black',linewidth=3,label='ATLAS')
axes.plot(contoursCM[1.0][0][:,0],contoursCM[1.0][0][:,1],linestyle='-',c='green',linewidth=3,label='CheckMATE (LO)')
axes.plot(contoursSMS[1.0][0][:,0],contoursSMS[1.0][0][:,1],linestyle='-',c='gray',linewidth=3,label='Felipe/SModelS (LO)')

axes.set_xlabel(r'$m_{\tilde{chi}_1^{\pm}}$ (GeV)')
axes.set_ylabel(r'$\tau_{\tilde{\chi}_1^\pm}$ (ns)')
axes.set_title(r'$\tilde{\chi}_1^\pm \tilde{\chi}_1^\mp + \tilde{\chi}_1^\pm \tilde{\chi}_1^0$')
axes.set_yscale('log')
axes.set_ylim(1e-2,10)

cb = fig.colorbar(ax,label=r'$\epsilon_{SMS}/\epsilon_{CM}$')
plt.legend(loc='upper left',framealpha=0.9)
plt.savefig("CMvsSMS.png")
