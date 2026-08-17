"""edgar_lever1b.py — clean Lever 1: susceptibility of industry-adjusted ROA on REAL US
timestamps, reported as a SIZE-CHANNEL decomposition (the attack/defense refinement):
  rho_raw  = corr(latency, ROA - industry mean)                 [total susceptibility]
  rho_size = corr(latency, ROA - ind.mean | log size)           [residual, size removed]
The gap is the size channel; corr(latency, size) shows big firms file early.
Cluster-bootstrap CIs over SIC2xyear groups; per-year rho_raw series."""
import numpy as np, pandas as pd
from scipy.stats import rankdata
P=pd.read_parquet('edgar_panel.parquet')
P=P[P['Assets']>0].dropna(subset=['NetIncomeLoss','Assets','sic','filed','end']).copy()
P['roa']=P['NetIncomeLoss']/P['Assets']; P['filed']=pd.to_datetime(P['filed']); P['end']=pd.to_datetime(P['end'])
P['lat']=(P['filed']-P['end']).dt.days; P=P[(P['lat']>0)&(P['lat']<200)]
P['sic2']=P['sic'].astype('Int64').astype(str).str.zfill(4).str[:2]; P['fy']=P['end'].dt.year
P['logA']=np.log(P['Assets'].clip(lower=1)); SEED=20260601

def gbuild(df):
    gs=[]
    for _,g in df.groupby(['sic2','fy']):
        if len(g)<20: continue
        roa=g['roa'].clip(g['roa'].quantile(.02),g['roa'].quantile(.98)).values
        gs.append((rankdata(g['lat'].values).astype(float), roa-roa.mean(), g['logA'].values-g['logA'].mean()))
    return gs

def rho(gs, ctrl):
    a=[];b=[]
    for lat,u,sz in gs:
        l=lat.copy(); uu=u.copy()
        if ctrl:
            X=np.column_stack([np.ones(len(l)),sz])
            l=l-X@np.linalg.lstsq(X,l,rcond=None)[0]; uu=uu-X@np.linalg.lstsq(X,uu,rcond=None)[0]
        if l.std()<1e-9 or uu.std()<1e-9: continue
        a.append((l-l.mean())/l.std()); b.append((uu-uu.mean())/uu.std())
    return np.corrcoef(np.concatenate(a),np.concatenate(b))[0,1]

gs=gbuild(P); print(f'groups(SIC2xyear>=20)={len(gs)}',flush=True)
rng=np.random.default_rng(SEED)
rraw=rho(gs,False); rsz=rho(gs,True)
G=len(gs); braw=[];bsz=[]
for _ in range(2000):
    samp=[gs[i] for i in rng.integers(0,G,G)]; braw.append(rho(samp,False)); bsz.append(rho(samp,True))
ci=lambda v:(np.percentile(v,2.5),np.percentile(v,97.5))
print(f'rho_raw  (total susceptibility)      = {rraw:+.3f}  95%CI[{ci(braw)[0]:+.3f},{ci(braw)[1]:+.3f}]',flush=True)
print(f'rho_size (size-controlled, residual) = {rsz:+.3f}  95%CI[{ci(bsz)[0]:+.3f},{ci(bsz)[1]:+.3f}]',flush=True)
# size mechanism
a=[];b=[]
for lat,u,sz in gs:
    a.append((lat-lat.mean())/lat.std()); b.append((sz-sz.mean())/(sz.std()+1e-9))
print(f'corr(latency, size) within group     = {np.corrcoef(np.concatenate(a),np.concatenate(b))[0,1]:+.3f}  (big firms file early)',flush=True)
print('\nper-year rho_raw (industry-adjusted ROA, observed dates):',flush=True)
for y in sorted(P.fy.unique()):
    gy=gbuild(P[P.fy==y])
    if len(gy)>=4: print(f'  {y}: {rho(gy,False):+.3f} (groups={len(gy)})',flush=True)
