#!/usr/bin/env python3

"""Plot validation results."""

# %% Imports
import os,glob
import pyslha
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
slhaFolder = '../data/TDTM1M2F_slha'
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
    eff = data['eff'][0]
    if eff:
        sigUL = 0.22/eff
    else:
        sigUL = -1.0
    if ns > 0:
        ds_rel = ds/ns
    else:
        ds_rel = ds/1.0
    rData.append([mC1,ctau_ns,data['robs'][0],data['robscons'][0],ds_rel,sigUL])

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

axes.plot(contours[1.0][0][:,0],contours[1.0][0][:,1],linestyle='--',c='gray',linewidth=3,label='CheckMATE (LO)')
axes.plot(contours[0.9][0][:,0],contours[0.9][0][:,1],linestyle='-.',c='gray',linewidth=3,label='CheckMATE (k = 1.1)')
axes.plot(contours[0.83][0][:,0],contours[0.83][0][:,1],linestyle='-',c='gray',linewidth=3,label='CheckMATE (k = 1.2)')

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
plt.savefig("atlas_susy_2016_06_ExcComp.png")



# %%
ULmap = np.genfromtxt('./UpperLimitEW.csv',names=True,skip_header=10,delimiter=',')
#The UL map is actually in pb!
ULATLAS = 1e3*ULmap['The_95__CL_s_upper_limits_on_the_production_crosssection_fb']


# %% Create grid for interpolating upper limits from recasting:
newpts = np.array(list(zip(ULmap['MCHARGINO1_GEV'],np.log10(ULmap['TAUCHARGINO1_NS']))))
ULmapRecast = griddata(list(zip(rData[:,0],np.log10(rData[:,1]))),rData[:,5],newpts)

## %% Get upper limit relative diff:
ULdiff = (ULmapRecast-ULATLAS)/ULATLAS

# %% plot results
fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(10,6))
ax = axes.scatter(ULmap['MCHARGINO1_GEV'],ULmap['TAUCHARGINO1_NS'],
    c=ULdiff,cmap=cm,vmin=-0.5,vmax=0.5,s=120)
axes.plot(excATLAS['mC1_GeV'], 6.582e-16/excATLAS['width_GeV'],linestyle='-',c='black',linewidth=3,label='ATLAS',alpha=0.5)
for i,pt in enumerate(ULdiff):
    axes.annotate('%1.1f'%pt,(ULmap['MCHARGINO1_GEV'][i],1.05*ULmap['TAUCHARGINO1_NS'][i]),
                    fontsize=15)


axes.set_xlabel(r'$m_{\tilde{chi}_1^{\pm}}$ (GeV)')
axes.set_ylabel(r'$\tau_{\tilde{\chi}_1^\pm}$ (ns)')
axes.set_title(r'$\tilde{\chi}_1^\pm \tilde{\chi}_1^\mp + \tilde{\chi}_1^\pm \tilde{\chi}_1^0$')
axes.set_yscale('log')
axes.set_xlim(120,650)
cb = fig.colorbar(ax,label=r'$r=\sigma/\sigma_UL$')
cb.set_label(r'$(\sigma_UL^{CM}-\sigma_UL^{ATLAS})/\sigma_UL^{ATLAS}$')
plt.savefig("atlas_susy_2016_06_ULcomp.png")
