#!/usr/bin/env python3

"""Plot validation results."""

# %% Imports
import os,glob
import pyslha
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

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
resultFolder = './data/TDTM1M2F_cm'
slhaFolder = './data/TDTM1M2F_slha'
rData = []
for slhaFile in glob.glob(slhaFolder+'/*.slha'):
    slhaData = pyslha.readSLHAFile(slhaFile)
    mC1 = slhaData.blocks['MASS'][1000024]
    widthC1 = slhaData.decays[1000024].totalwidth
    resDir = os.path.splitext(os.path.basename(slhaFile))[0]
    resFile = os.path.join(resultFolder,resDir,'evaluation',
                'total_results.txt')
    if not os.path.isfile(resFile):
        # print('skipping',slhaFile)
        continue
    data = np.genfromtxt(resFile,names=True,dtype=None,encoding=None)
    data = data[data['sr'] == 'SR1'] #Select (unique) signal region
    ctau_ns = 6.582e-16/widthC1
    ns = data['s'][0]
    ds = data['ds'][0]
    if ns > 0:
        ds_rel = ds/ns
    else:
        ds_rel = ds/1.0
    rData.append([mC1,ctau_ns,data['robs'][0],ds_rel])

rData = np.array(rData)

# %%
print(excATLAS.dtype)

# %% plot results
fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(18,8))
ax = axes[0].scatter(rData[:,0],rData[:,1],
    c=rData[:,2],cmap=cm,vmin=0.0,vmax=2.0,s=120)

axes[0].plot(excATLAS['mC1_GeV'], 6.582e-16/excATLAS['width_GeV'],linestyle='-',c='b')

axes[0].set_xlabel(r'$m_{\tilde{chi}_1^{\pm}}$ (GeV)')
axes[0].set_ylabel(r'$\tau_{\tilde{\chi}_1^\pm}$ (ns)')
axes[0].set_title(r'$\tilde{\chi}_1^\pm \tilde{\chi}_1^\mp + \tilde{\chi}_1^\pm + \tilde{\chi}_1^0$')
axes[0].set_yscale('log')

ax = axes[1].scatter(rData[:,0],rData[:,1],
    c=rData[:,-1],cmap=cm,vmin=0.0,vmax=2.0,s=120)
axes[1].set_xlabel(r'$m_{\tilde{chi}_1^{\pm}}$ (GeV)')
axes[1].set_ylabel(r'$\tau_{\tilde{\chi}_1^\pm}$ (ns)')

cb = fig.colorbar(ax, ax=axes.ravel().tolist())
cb.set_label(r'$r$')
plt.savefig("atlas_susy_2016_06_CM.png")




## %% Get exclusion contours for signal
contoursHigh = getContour(rData[:,0],rData[:,1],rData[:,2],levels=[1.0])
contoursLow = getContour(rData[:,0],rData[:,1],rData[:,3],levels=[1.0])

# %% Load data
offCurveComb = np.genfromtxt('./ATLAS_data/HEPData-ins1765529-v1-Exclusion_contour_1_Obs.csv',
                        delimiter=',', names=True, skip_header=10)
offCurveLow = np.genfromtxt('./ATLAS_data/HEPData-ins1765529-v1-Exclusion_contour_aux_1_Obs.csv',
                        delimiter=',', names=True, skip_header=10)
offCurveHigh = np.genfromtxt('./ATLAS_data/HEPData-ins1765529-v1-Exclusion_contour_aux_2_Obs.csv',
                        delimiter=',', names=True, skip_header=10)

# %% Plot exclusion curve
fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(18,8))
ax = axes[0].scatter(rData[:,0],rData[:,1],
    c=rData[:,2],cmap=cm,vmin=0.0,vmax=2.0,s=70)
for level,curves in contoursHigh.items():
    for curve in curves:
        axes[0].plot(curve[:,0],curve[:,1],label='Recast (r = %s)' %str(level),linestyle='--',linewidth=4)
axes[0].plot(offCurveHigh['MSTAU_GeV'],offCurveHigh['MNEUTRALINO1_GeV'],linewidth=4,
        color='black',label='ATLAS-SUSY-2018-04 (High Mass)')

ax = axes[1].scatter(rData[:,0],rData[:,1],
    c=rData[:,3],cmap=cm,vmin=0.0,vmax=2.0,s=70)
for level,curves in contoursLow.items():
    for curve in curves:
        axes[1].plot(curve[:,0],curve[:,1],label='Recast (r = %s)' %str(level),linestyle='--',linewidth=4)
axes[1].plot(offCurveLow['MSTAU_GeV'],offCurveLow['MNEUTRALINO1_GeV'],linewidth=4,
        color='black',label='ATLAS-SUSY-2018-04 (Low Mass)')
axes[0].legend()
axes[0].set_xlabel(r'$m_{\tilde{\tau}}$ (GeV)')
axes[0].set_ylabel(r'$m_{\tilde{\chi}_1^0}$ (GeV)')
axes[0].set_title(r'$\tilde{\tau} \tilde{\tau}, \tilde{\tau} \to \tau + \tilde{\chi}_1^0$ (SR-HighMass)')
axes[1].legend()
axes[1].set_xlabel(r'$m_{\tilde{\tau}}$ (GeV)')
axes[1].set_title(r'$\tilde{\tau} \tilde{\tau}, \tilde{\tau} \to \tau + \tilde{\chi}_1^0$ (SR-lowMass)')

cb = fig.colorbar(ax, ax=axes.ravel().tolist())
cb.set_label(r'$r = \sigma/\sigma_{UL}^{95}$')
plt.savefig("atlas_susy_2018_04_Stau.png")
plt.show()
