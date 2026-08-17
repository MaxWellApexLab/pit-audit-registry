"""edgar_ci.py — cluster-bootstrap 95% CIs for the size-partialled rho_hat of every signal.

edgar_lever23.py prints the point estimates only. A verdict against a 0.10 threshold is not
defensible without knowing whether the interval clears it, so this recomputes rho_size per
signal with the same estimator and a cluster bootstrap over SIC2 x fiscal-year groups.
"""
import numpy as np, pandas as pd
from scipy.stats import rankdata

SEED = 20260601
BBOOT = 1000
RHO_THRESHOLD = 0.10
PHI_MIN, KAPPA = 0.35, 1.0

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
        if len(g) < 20:
            continue
        s = g['s'].clip(g['s'].quantile(.02), g['s'].quantile(.98)).values
        gs.append((rankdata(g['lat'].values).astype(float),
                   s - s.mean(),
                   g['logA'].values - g['logA'].mean()))
    return gs


def rho(gs, ctrl):
    a, b = [], []
    for lat, u, sz in gs:
        l, uu = lat.copy(), u.copy()
        if ctrl:
            X = np.column_stack([np.ones(len(l)), sz])
            l = l - X @ np.linalg.lstsq(X, l, rcond=None)[0]
            uu = uu - X @ np.linalg.lstsq(X, uu, rcond=None)[0]
        if l.std() < 1e-9 or uu.std() < 1e-9:
            continue
        a.append((l - l.mean()) / l.std())
        b.append((uu - uu.mean()) / uu.std())
    if not a:
        return np.nan
    return float(np.corrcoef(np.concatenate(a), np.concatenate(b))[0, 1])


rng = np.random.default_rng(SEED)
print(f"{'signal':20}{'rho_raw':>9}{'rho_size':>10}{'95% CI (rho_size)':>22}"
      f"{'phi_req':>9}  verdict")
out = []
for nm, fn in SIGDEF.items():
    d = P.copy(); d['s'] = fn(d)
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=['s'])
    gs = gbuild(d)
    r_raw, r_sz = rho(gs, False), rho(gs, True)
    G = len(gs)
    boot = [rho([gs[i] for i in rng.integers(0, G, G)], True) for _ in range(BBOOT)]
    boot = [b for b in boot if not np.isnan(b)]
    lo, hi = np.percentile(boot, 2.5), np.percentile(boot, 97.5)
    # a flag survives uncertainty only if the whole interval is outside +-threshold
    ci_clears = (lo > RHO_THRESHOLD) or (hi < -RHO_THRESHOLD)
    point_flags = abs(r_sz) > RHO_THRESHOLD
    phi = min(1.0, PHI_MIN + KAPPA * abs(r_sz))
    verdict = ('susceptible' if ci_clears else
               'inconclusive' if point_flags else 'benign')
    out.append((nm, r_raw, r_sz, lo, hi, phi, verdict, G))
    print(f'{nm:20}{r_raw:>+9.3f}{r_sz:>+10.3f}{f"[{lo:+.3f}, {hi:+.3f}]":>22}'
          f'{phi:>9.2f}  {verdict}')

nb = sum(1 for o in out if o[6] == 'benign')
ni = sum(1 for o in out if o[6] == 'inconclusive')
ns = sum(1 for o in out if o[6] == 'susceptible')
print(f'\nbenign {nb} | inconclusive {ni} | susceptible {ns}  (of {len(out)} signals)')
print(f'threshold |rho|>{RHO_THRESHOLD}; "susceptible" requires the whole 95% CI '
      f'to clear the threshold, "inconclusive" = point estimate over but CI straddles it.')
