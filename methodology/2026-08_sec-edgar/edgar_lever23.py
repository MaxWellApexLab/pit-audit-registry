"""
edgar_lever23.py — Levers 2 & 3 on the real US as-filed panel.
 (3) FACTOR-ZOO SUSCEPTIBILITY MAP: for ~14 industry-adjusted cross-sectional signals,
     ex-post rho_hat (susceptibility) and matched decile-reassignment excess.
 (2) OUT-OF-SAMPLE VALIDATION: estimate rho_hat on TRAIN years, predict the matched
     excess on held-out TEST years across signals -> genuine prediction, not in-sample
     co-movement (the residual is no longer shared across the train/test split).
All on OBSERVED filing dates; no returns needed.
"""
import numpy as np, pandas as pd
from scipy.stats import rankdata, spearmanr
P0=pd.read_parquet('edgar_panel.parquet')
SEED=20260601; FRAC=0.35; NCTRL=8; TRAIN_MAX=2017

def prep(P):
    P=P.copy(); P=P[P['Assets']>0]
    rev=P['Revenues'].fillna(P['RevenueFromContractWithCustomerExcludingAssessedTax']).fillna(P['SalesRevenueNet'])
    P['rev']=rev
    P['filed']=pd.to_datetime(P['filed']); P['end']=pd.to_datetime(P['end'])
    P['lat']=(P['filed']-P['end']).dt.days; P=P[(P['lat']>0)&(P['lat']<200)]
    P['sic2']=P['sic'].astype('Int64').astype(str).str.zfill(4).str[:2]
    P['fy']=P['end'].dt.year; P['logA']=np.log(P['Assets'].clip(lower=1))
    P=P.sort_values(['cik','end'])
    for col,new in [('Assets','Assets_l'),('rev','rev_l')]:
        P[new]=P.groupby('cik')[col].shift(1)
    return P

def signal(P,name):
    d=P.copy()
    if   name=='ROA': d['s']=d['NetIncomeLoss']/d['Assets']
    elif name=='CFO/assets': d['s']=d['NetCashProvidedByUsedInOperatingActivities']/d['Assets']
    elif name=='GrossProfit/assets': d['s']=d['GrossProfit']/d['Assets']
    elif name=='OpProfit/assets': d['s']=d['OperatingIncomeLoss']/d['Assets']
    elif name=='Accruals': d['s']=(d['NetIncomeLoss']-d['NetCashProvidedByUsedInOperatingActivities'])/d['Assets']
    elif name=='NetMargin': d['s']=d['NetIncomeLoss']/d['rev']
    elif name=='AssetGrowth': d['s']=(d['Assets']-d['Assets_l'])/d['Assets_l']
    elif name=='SalesGrowth': d['s']=(d['rev']-d['rev_l'])/d['rev_l'].abs()
    elif name=='Inventory/assets': d['s']=d['InventoryNet']/d['Assets']
    elif name=='PPE/assets': d['s']=d['PropertyPlantAndEquipmentNet']/d['Assets']
    elif name=='Leverage': d['s']=d['Liabilities']/d['Assets']
    elif name=='Equity/assets': d['s']=d['StockholdersEquity']/d['Assets']
    elif name=='RnD/assets': d['s']=d['ResearchAndDevelopmentExpense']/d['Assets']
    elif name=='CurrentRatio': d['s']=d['AssetsCurrent']/d['LiabilitiesCurrent']
    d=d.replace([np.inf,-np.inf],np.nan).dropna(subset=['s'])
    return d

def groups(d):
    gs=[]
    for (s,y),g in d.groupby(['sic2','fy']):
        if len(g)<20: continue
        g=g.reset_index(drop=True); n=len(g)
        lo,hi=g['s'].quantile(.02),g['s'].quantile(.98); sv=g['s'].clip(lo,hi).values
        gs.append(dict(n=n,s=sv,sB=sv-sv.mean(),lat=rankdata(g['lat'].values)/n,
                       logA=g['logA'].values,order=np.argsort(g['lat'].values),fy=y))
    return gs

def rho(gs, ctrl=False):
    """ctrl=False: total susceptibility of the as-traded industry-adjusted signal
       (construction has no firm-level regressors, so no size partial -- see diagnostic).
       ctrl=True: residual after removing observable size."""
    a=[];b=[]
    for g in gs:
        rl=g['lat'].copy(); ru=g['sB'].copy()
        if ctrl:
            X=np.column_stack([np.ones(g['n']),g['logA']-g['logA'].mean()])
            rl=rl-X@np.linalg.lstsq(X,rl,rcond=None)[0]; ru=ru-X@np.linalg.lstsq(X,ru,rcond=None)[0]
        if rl.std()<1e-9 or ru.std()<1e-9: continue
        a.append((rl-rl.mean())/rl.std()); b.append((ru-ru.mean())/ru.std())
    if not a: return np.nan
    return np.corrcoef(np.concatenate(a),np.concatenate(b))[0,1]

def dec(v): return pd.qcut(pd.Series(v).rank(method='first'),10,labels=False).to_numpy()
def excess(gs,rng,frac=FRAC):
    def pooled(mode):
        sa=[];sb=[]
        for g in gs:
            n=g['n']; k=max(6,int(round(frac*n)))
            if k>=n: continue
            if mode=='date': m=np.zeros(n,bool); m[g['order'][:k]]=True
            else:
                la=g['logA']; s=(la-la.mean())/(la.std()+1e-9); ew=s[g['order'][:k]].mean()
                w=np.exp(-2*np.abs(s-ew)); w/=w.sum(); idx=rng.choice(n,k,replace=False,p=w); m=np.zeros(n,bool); m[idx]=True
            sv=g['s'][m]; sa.append(sv-sv.mean()); sb.append(g['sB'][m])
        sa=np.concatenate(sa); sb=np.concatenate(sb); return float((dec(sa)!=dec(sb)).mean())
    fd=pooled('date'); fm=np.mean([pooled('match') for _ in range(NCTRL)])
    return fd-fm

SIGS=['ROA','CFO/assets','GrossProfit/assets','OpProfit/assets','NetMargin','Accruals',
      'AssetGrowth','SalesGrowth','Inventory/assets','PPE/assets','Leverage','Equity/assets','RnD/assets','CurrentRatio']

if __name__=='__main__':
    P=prep(P0); rng=np.random.default_rng(SEED)
    print(f'US panel {len(P)} firm-years {P.cik.nunique()} firms {P.fy.min()}-{P.fy.max()}',flush=True)
    print('\n=== Lever 3: factor-zoo susceptibility map (full sample) ===',flush=True)
    print(f"{'signal':20} {'rho_raw':>8} {'rho_size':>9} {'xi_match(pp)':>12}",flush=True)
    full=[]
    for nm in SIGS:
        d=signal(P,nm); gs=groups(d)
        if len(gs)<10: print(f'{nm:20} (few groups)'); continue
        r=rho(gs,False); rs=rho(gs,True); xi=100*excess(gs,rng)
        full.append((nm,r,rs,xi)); print(f'{nm:20} {r:+8.3f} {rs:+9.3f} {xi:+12.2f}',flush=True)
    fr=np.array([x[1] for x in full]); fx=np.array([x[3] for x in full])
    sp=spearmanr(fr,fx)
    print(f'\nfull-sample Spearman(rho_raw, xi_match) over {len(full)} signals = {sp[0]:+.3f} (p={sp[1]:.4f})',flush=True)
    print(f'(rho_raw = total as-traded susceptibility; rho_size = residual after removing observable size.)',flush=True)

    print('\n=== Lever 2: OUT-OF-SAMPLE (train rho_hat <=%d, predict test xi_match >%d) ==='%(TRAIN_MAX,TRAIN_MAX),flush=True)
    print(f"{'signal':20} {'train_rho':>9} {'test_xi(pp)':>11}",flush=True)
    oos=[]
    for nm in SIGS:
        d=signal(P,nm)
        gtr=groups(d[d.fy<=TRAIN_MAX]); gte=groups(d[d.fy>TRAIN_MAX])
        if len(gtr)<8 or len(gte)<8: continue
        tr=rho(gtr,False); te=100*excess(gte,rng); ter=rho(gte,False)
        oos.append((nm,tr,te,ter)); print(f'{nm:20} {tr:+9.3f} {te:+11.2f}',flush=True)
    tr=np.array([x[1] for x in oos]); te=np.array([x[2] for x in oos]); ter=np.array([x[3] for x in oos])
    spo=spearmanr(tr,te); spr=spearmanr(tr,ter)
    print(f'\nOUT-OF-SAMPLE Spearman(train rho_raw, test xi_match) over {len(oos)} signals = {spo[0]:+.3f} (p={spo[1]:.4f})',flush=True)
    print(f'OUT-OF-SAMPLE Spearman(train rho_raw, test rho_raw)   over {len(oos)} signals = {spr[0]:+.3f} (p={spr[1]:.4f})',flush=True)
    print('(>0 in magnitude with the same sign as in-sample => the screen estimated on PAST data predicts reordering on UNSEEN years -> genuine validation, not shared-residual co-movement.)',flush=True)
