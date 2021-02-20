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
resultFolder = '../data/TDTM1M2F_smodels'
slhaFolder = '../data/TDTM1M2F_slha'
rData = []
for slhaFile in glob.glob(slhaFolder+'/*.slha'):
    slhaData = pyslha.readSLHAFile(slhaFile)
    mC1 = slhaData.blocks['MASS'][1000024]
    widthC1 = slhaData.decays[1000024].totalwidth
    ctau_ns = 6.582e-16/widthC1
    xsecC1C1 = [x for x in slhaData.xsections[(2212,2212,-1000024,1000024)].xsecs if x.sqrts == 13000.][0].value
    xsecC1pN1 = [x for x in slhaData.xsections[(2212,2212,1000022,1000024)].xsecs if x.sqrts == 13000.][0].value
    xsecC1mN1 = [x for x in slhaData.xsections[(2212,2212,-1000024,1000022)].xsecs if x.sqrts == 13000.][0].value
    xsectot_fb = (xsecC1C1+xsecC1pN1+xsecC1mN1)*1e3
    basename =os.path.basename(slhaFile)
    resFile = os.path.join(resultFolder,basename+'.py')
    if not os.path.isfile(resFile):
        # print('skipping',slhaFile)
        continue
    smodelsDict = imp.load_source(resFile.replace('.py',''),resFile).smodelsOutput
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
    rData.append([mC1,ctau_ns,r,sigUL])

rData = np.array(rData)

# %%
print(excATLAS.dtype)

## %% Get exclusion contours for signal
contours = getContour(rData[:,0],rData[:,1],rData[:,2],levels=[0.83,0.9,1.0],ylog=True)


# %% plot results
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(10,6))
ax = axes.scatter(rData[:,0],rData[:,1],
    c=rData[:,2],cmap=cm,vmin=0.0,vmax=2.0,s=120)

axes.plot(excATLAS['mC1_GeV'], 6.582e-16/excATLAS['width_GeV'],linestyle='-',c='black',linewidth=3,label='ATLAS')

axes.plot(contours[1.0][0][:,0],contours[1.0][0][:,1],linestyle='--',c='gray',linewidth=3,label='SModelS (LO)')
axes.plot(contours[0.9][0][:,0],contours[0.9][0][:,1],linestyle='-.',c='gray',linewidth=3,label='SModelS (k = 1.1)')

axes.set_xlabel(r'$m_{\tilde{chi}_1^{\pm}}$ (GeV)')
axes.set_ylabel(r'$\tau_{\tilde{\chi}_1^\pm}$ (ns)')
axes.set_title(r'$\tilde{\chi}_1^\pm \tilde{\chi}_1^\mp + \tilde{\chi}_1^\pm \tilde{\chi}_1^0$')
axes.set_yscale('log')

# ax = axes[1].scatter(rData[:,0],rData[:,1],
    # c=rData[:,-1],cmap=cm,vmin=0.0,vmax=2.0,s=120)
# axes[1].set_xlabel(r'$m_{\tilde{chi}_1^{\pm}}$ (GeV)')
# axes[1].set_ylabel(r'$\tau_{\tilde{\chi}_1^\pm}$ (ns)')

cb = fig.colorbar(ax,label=r'$r=\sigma/\sigma_UL$')
cb.set_label(r'$r$')
plt.legend(loc='lower right',framealpha=0.9)
plt.savefig("SModelSExc.png")



# %%
ULmap = np.genfromtxt('./UpperLimitEW.csv',names=True,skip_header=10,delimiter=',')
#The UL map is actually in pb!
ULATLAS = 1e3*ULmap['The_95__CL_s_upper_limits_on_the_production_crosssection_fb']


# %% Create grid for interpolating upper limits from recasting:
newpts = np.array(list(zip(ULmap['MCHARGINO1_GEV'],np.log10(ULmap['TAUCHARGINO1_NS']))))
ULmapRecast = griddata(list(zip(rData[:,0],np.log10(rData[:,1]))),rData[:,3],newpts)

## %% Get upper limit relative diff:
ULdiff = (ULmapRecast-ULATLAS)/ULATLAS

# %% plot results
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(10,6))
ax = axes.scatter(ULmap['MCHARGINO1_GEV'],ULmap['TAUCHARGINO1_NS'],
    c=ULdiff,cmap=cm,vmin=-0.5,vmax=0.5,s=120)
axes.plot(excATLAS['mC1_GeV'], 6.582e-16/excATLAS['width_GeV'],linestyle='-',c='black',linewidth=3,label='ATLAS',alpha=0.5)
for i,pt in enumerate(ULdiff):
    axes.annotate('%1.2f'%pt,(ULmap['MCHARGINO1_GEV'][i],1.1*ULmap['TAUCHARGINO1_NS'][i]),
                    fontsize=15)


axes.set_xlabel(r'$m_{\tilde{chi}_1^{\pm}}$ (GeV)')
axes.set_ylabel(r'$\tau_{\tilde{\chi}_1^\pm}$ (ns)')
axes.set_title(r"$\tilde{\chi}_1^\pm \tilde{\chi}_1^\mp + \tilde{\chi}_1^\pm \tilde{\chi}_1^0$ (Felipe's)")
axes.set_yscale('log')
axes.set_xlim(120,650)
cb = fig.colorbar(ax,label=r'$r=\sigma/\sigma_UL$')
cb.set_label(r'$(\sigma_{UL}^{SMS}-\sigma_{UL}^{ATLAS})/\sigma_{UL}^{ATLAS}$')
plt.savefig("SMSvsATLAS.png")
