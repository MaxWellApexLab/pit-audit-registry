"""edgar_frozen.py — run the registry's OWN screen protocol on the EDGAR panel.

edgar_lever23.py reports EX POST, full-sample rho_hat. The OSAP registry entry instead
grades each cycle with a FROZEN estimate fitted on the K completed cycles before it, which
is the protocol the registry documents. This script applies that protocol here so the two
reports are comparable, and reports flagged/screened per signal in signal-cycles.

Protocol (identical to the OSAP entry):
    rho_hat for year Y  = pooled partial corr(latency rank, signal | log size)
                          over years Y-K .. Y-1, frozen, then applied to Y
    flagged if |rho_hat| > 0.10 ; phi_req = min(1, 0.35 + 1.0*|rho_hat|)
"""
import numpy as np, pandas as pd
from scipy.stats import rankdata

K = 5
N_EVAL = 6
RHO_THRESHOLD = 0.10
PHI_MIN, KAPPA = 0.35, 1.0
MIN_GROUP = 20

P = pd.read_parquet('edgar_panel.parquet')
P = P[P['Assets'] > 0].copy()
P['rev'] = (P['Revenues'].fillna(P['RevenueFromContractWithCustomerExcludingAssessedTax'])
            .fillna(P['SalesRevenueNet']))
P['filed'] = pd.to_datetime(P['filed']); P['end'] = pd.to_datetime(P['end'])
P['lat'] = (P['filed'] - P['end']).dt.days
P = P[(P['lat'] > 0) & (P['lat'] < 200)]
P['sic2'] = P['sic'].astype('Int64').astype(str).str.zfill(4).str[:2]
P['fy'] = P['end'].dt.year
P['logA'] = np.log(P['Assets'].clip(lower=1))
P = P.sort_values(['cik', 'end'])
P['Assets_l'] = P.groupby('cik')['Assets'].shift(1)
P['rev_l'] = P.groupby('cik')['rev'].shift(1)

SIGDEF = {
    'ROA':                 lambda d: d['NetIncomeLoss'] / d['Assets'],
    'CFO/assets':          lambda d: d['NetCashProvidedByUsedInOperatingActivities'] / d['Assets'],
    'GrossProfit/assets':  lambda d: d['GrossProfit'] / d['Assets'],
    'OpProfit/assets':     lambda d: d['OperatingIncomeLoss'] / d['Assets'],
    'NetMargin':           lambda d: d['NetIncomeLoss'] / d['rev'],
    'Accruals':            lambda d: (d['NetIncomeLoss'] - d['NetCashProvidedByUsedInOperatingActivities']) / d['Assets'],
    'AssetGrowth':         lambda d: (d['Assets'] - d['Assets_l']) / d['Assets_l'],
    'SalesGrowth':         lambda d: (d['rev'] - d['rev_l']) / d['rev_l'].abs(),
    'Inventory/assets':    lambda d: d['InventoryNet'] / d['Assets'],
    'PPE/assets':          lambda d: d['PropertyPlantAndEquipmentNet'] / d['Assets'],
    'Leverage':            lambda d: d['Liabilities'] / d['Assets'],
    'Equity/assets':       lambda d: d['StockholdersEquity'] / d['Assets'],
    'RnD/assets':          lambda d: d['ResearchAndDevelopmentExpense'] / d['Assets'],
    'CurrentRatio':        lambda d: d['AssetsCurrent'] / d['LiabilitiesCurrent'],
}


def gbuild(df):
    gs = []
    for _, g in df.groupby(['sic2', 'fy']):
        if len(g) < MIN_GROUP:
            continue
        s = g['s'].clip(g['s'].quantile(.02), g['s'].quantile(.98)).values
        gs.append((rankdata(g['lat'].values).astype(float),
                   s - s.mean(),
                   g['logA'].values - g['logA'].mean()))
    return gs


def rho(gs):
    a, b = [], []
    for lat, u, sz in gs:
        X = np.column_stack([np.ones(len(lat)), sz])
        l = lat - X @ np.linalg.lstsq(X, lat, rcond=None)[0]
        uu = u - X @ np.linalg.lstsq(X, u, rcond=None)[0]
        if l.std() < 1e-9 or uu.std() < 1e-9:
            continue
        a.append((l - l.mean()) / l.std())
        b.append((uu - uu.mean()) / uu.std())
    if not a:
        return np.nan
    return float(np.corrcoef(np.concatenate(a), np.concatenate(b))[0, 1])


print(f'FROZEN protocol: K={K} trailing years, {N_EVAL} evaluation years, '
      f'threshold |rho|>{RHO_THRESHOLD}, phi_min={PHI_MIN}, kappa={KAPPA}\n')

summary, detail = [], []
for nm, fn in SIGDEF.items():
    d = P.copy(); d['s'] = fn(d)
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=['s'])
    years = sorted(y for y in d.fy.unique() if len(gbuild(d[d.fy == y])) >= 3)
    evals = [y for y in years if len([x for x in years if y - K <= x < y]) == K][-N_EVAL:]
    rows = []
    for y in evals:
        prior = [x for x in years if y - K <= x < y]
        r_frozen = rho(gbuild(d[d.fy.isin(prior)]))
        r_expost = rho(gbuild(d[d.fy == y]))
        n = int(d[d.fy == y].shape[0])
        if np.isnan(r_frozen):
            continue
        flagged = abs(r_frozen) > RHO_THRESHOLD
        rows.append(dict(signal=nm, year=y, n=n, rho_frozen=r_frozen,
                         flagged=flagged, phi_req=min(1.0, PHI_MIN + KAPPA * abs(r_frozen)),
                         rho_expost=r_expost))
    if not rows:
        continue
    detail += rows
    rf = np.array([r['rho_frozen'] for r in rows])
    summary.append(dict(signal=nm, mean_rho=rf.mean(), max_abs=np.abs(rf).max(),
                        flagged=sum(r['flagged'] for r in rows), screened=len(rows),
                        mean_phi=np.mean([r['phi_req'] for r in rows])))

print(f"{'signal':20}{'mean rho':>10}{'max|rho|':>10}{'flagged/screened':>19}{'mean phi_req':>14}  verdict")
tot_f = tot_s = 0
for s in summary:
    v = 'susceptible' if s['flagged'] else 'benign'
    tot_f += s['flagged']; tot_s += s['screened']
    mark = '*' if s['flagged'] else ' '
    ratio = f"{mark}{s['flagged']} / {s['screened']}"
    print(f"{s['signal']:20}{s['mean_rho']:>+10.4f}{s['max_abs']:>10.4f}{ratio:>19}"
          f"{s['mean_phi']:>14.2f}  {v}")

print(f'\nTOTAL: {tot_f} flagged of {tot_s} signal-cycles across {len(summary)} signals')
print(f'signals with zero flagged cycles: {sum(1 for s in summary if not s["flagged"])} / {len(summary)}')

print('\n=== per-cycle detail ===')
print(f"{'signal':20}{'year':>6}{'n':>7}{'rho (frozen)':>14}{'flagged':>9}{'phi_req':>9}{'rho (ex post)':>15}")
for r in detail:
    print(f"{r['signal']:20}{r['year']:>6}{r['n']:>7}{r['rho_frozen']:>+14.4f}"
          f"{('yes' if r['flagged'] else 'no'):>9}{r['phi_req']:>9.2f}{r['rho_expost']:>+15.4f}")
