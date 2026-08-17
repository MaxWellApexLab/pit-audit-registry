"""
edgar_lever1.py — Lever 1: full US signal-level identification on REAL observed
timestamps. Industry-adjusted ROA = NetIncomeLoss/Assets, industry = SIC 2-digit.
Within (SIC2 x fiscal-year) groups computes, on OBSERVED filing dates:
  * rho_hat = partial corr(filing-latency rank, signal residual | log size), cluster-bootstrap CI
  * matched/size-only excess (early-35% vs complete decile reassignment), cluster-bootstrap CI
Reports pooled values + a per-year rho_hat series. No returns needed (identification core).
"""
import numpy as np, pandas as pd
from scipy.stats import rankdata
P0=pd.read_parquet('edgar_panel.parquet')
SEED=20260601; FRAC=0.35; NCTRL=8; BBOOT=1000

def deciles(v): return pd.qcut(pd.Series(v).rank(method='first'),10,labels=False).to_numpy()

def prep(P):
    P=P.copy()
    P=P[P['Assets']>0]; P=P.dropna(subset=['NetIncomeLoss','Assets','sic','filed','end'])
    P['roa']=P['NetIncomeLoss']/P['Assets']
    P['filed']=pd.to_datetime(P['filed']); P['end']=pd.to_datetime(P['end'])
    P['lat']=(P['filed']-P['end']).dt.days
    P=P[(P['lat']>0)&(P['lat']<200)]
    P['sic2']=(P['sic'].astype('Int64').astype(str).str.zfill(4).str[:2])
    P['fy']=P['end'].dt.year; P['logA']=np.log(P['Assets'].clip(lower=1))
    return P

def groups(P):
    gs=[]
    for (s,y),g in P.groupby(['sic2','fy']):
        if len(g)<20: continue
        g=g.reset_index(drop=True); n=len(g)
        lo,hi=g['roa'].quantile(.02),g['roa'].quantile(.98); roa=g['roa'].clip(lo,hi).values
        sB=roa-roa.mean()                      # complete industry-adjusted signal
        order=np.argsort(g['lat'].values)      # earliest filers first
        # propensity on size for matched control
        gs.append(dict(n=n,roa=roa,sB=sB,lat=rankdata(g['lat'].values)/n,
                       logA=g['logA'].values,order=order))
    return gs

def flip_excess(gs,rng,frac=FRAC):
    def pooled(mode):
        sa=[];sb=[]
        for g in gs:
            n=g['n']; k=max(6,int(round(frac*n)))
            if k>=n: continue
            if mode=='date': m=np.zeros(n,bool); m[g['order'][:k]]=True
            elif mode=='rand': idx=rng.choice(n,k,replace=False); m=np.zeros(n,bool); m[idx]=True
            else:
                la=g['logA']; s=(la-la.mean())/(la.std()+1e-9)
                # matched: sample by size-propensity resembling early set's size profile
                ews=s[g['order'][:k]].mean()
                w=np.exp(-2*np.abs(s-ews)); w=w/w.sum()
                idx=rng.choice(n,k,replace=False,p=w); m=np.zeros(n,bool); m[idx]=True
            roa=g['roa'][m]; sa.append(roa-roa.mean()); sb.append(g['sB'][m])
        sa=np.concatenate(sa); sb=np.concatenate(sb)
        return float((deciles(sa)!=deciles(sb)).mean())
    fd=pooled('date'); fr=np.mean([pooled('rand') for _ in range(NCTRL)]); fm=np.mean([pooled('match') for _ in range(NCTRL)])
    return fd,fr,fm

def rho(gs):
    a=[];b=[]
    for g in gs:
        X=np.column_stack([np.ones(g['n']),(g['logA']-g['logA'].mean())])
        bl,*_=np.linalg.lstsq(X,g['lat'],rcond=None); rl=g['lat']-X@bl
        bu,*_=np.linalg.lstsq(X,g['sB'],rcond=None); ru=g['sB']-X@bu
        if rl.std()<1e-9 or ru.std()<1e-9: continue
        a.append((rl-rl.mean())/rl.std()); b.append((ru-ru.mean())/ru.std())
    A=np.concatenate(a); B=np.concatenate(b); return np.corrcoef(A,B)[0,1]

if __name__=='__main__':
    P=prep(P0); print(f'US panel: {len(P)} firm-years, {P.cik.nunique()} firms, {P.sic2.nunique()} SIC2, {P.fy.min()}-{P.fy.max()}',flush=True)
    gs=groups(P); print(f'estimation groups (SIC2 x year, >=20): {len(gs)}',flush=True)
    rng=np.random.default_rng(SEED)
    fd,fr,fm=flip_excess(gs,rng)
    rh=rho(gs)
    print(f'\nINDUSTRY-ADJUSTED ROA (US, observed timestamps):',flush=True)
    print(f'  rho_hat(latency, signal | size) = {rh:+.3f}',flush=True)
    print(f'  decile-flip: date={100*fd:.1f}%  random={100*fr:.1f}%  matched={100*fm:.1f}%',flush=True)
    print(f'  xi_size={100*(fd-fr):+.2f}pp  xi_match={100*(fd-fm):+.2f}pp',flush=True)
    # cluster bootstrap over groups
    G=len(gs); xs=[];xm=[];rr=[]
    for _ in range(BBOOT):
        idx=rng.integers(0,G,G); samp=[gs[i] for i in idx]
        d,r,m=flip_excess(samp,rng); xs.append(d-r); xm.append(d-m); rr.append(rho(samp))
    ci=lambda v:(np.percentile(v,2.5),np.percentile(v,97.5))
    print(f'  cluster-bootstrap 95% CI: xi_size[{100*ci(xs)[0]:+.2f},{100*ci(xs)[1]:+.2f}] xi_match[{100*ci(xm)[0]:+.2f},{100*ci(xm)[1]:+.2f}] rho[{ci(rr)[0]:+.3f},{ci(rr)[1]:+.3f}]',flush=True)
    # per-year rho
    print('\nper-year industry-adjusted rho_hat:',flush=True)
    for y in sorted(P.fy.unique()):
        gy=groups(P[P.fy==y])
        if len(gy)>=5:
            print(f'  {y}: rho={rho(gy):+.3f}  (groups={len(gy)})',flush=True)
