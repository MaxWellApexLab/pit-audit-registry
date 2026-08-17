"""edgar_control.py — mandatory positive control for the SEC EDGAR audit, plus the
signal-cycle count used by the registry badge.

The control plants a known answer into cross-sections shaped like the real EDGAR panel
(same number of SIC2 x fiscal-year groups, same group-size distribution) and runs the
IDENTICAL estimator used on the real data (edgar_lever1b.rho with ctrl=True, i.e. the
size-partialled rho_hat). Two knobs:
    c_a -> selection on the UNOBSERVED disturbance   (the true leakage knob)
    c_x -> selection on the OBSERVED covariate, size (the benign kind)
The discriminating case is c_a=0, c_x=2.0: selected violently on an observable, which the
screen must still call benign.
"""
import numpy as np, pandas as pd
from scipy.stats import rankdata

SEED = 20260601
RHO_THRESHOLD = 0.10
PHI_MIN, KAPPA = 0.35, 1.0

# ---- real panel: group shapes and the signal x fiscal-year cell count -------------------
P = pd.read_parquet('edgar_panel.parquet')
P = P[P['Assets'] > 0].copy()
rev = (P['Revenues'].fillna(P['RevenueFromContractWithCustomerExcludingAssessedTax'])
       .fillna(P['SalesRevenueNet']))
P['rev'] = rev
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

print('=== signal x fiscal-year cells actually screened (registry badge count) ===')
cells_total = 0
rows = []
for nm, fn in SIGDEF.items():
    d = P.copy()
    d['s'] = fn(d)
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=['s'])
    years = set()
    ngroups = 0
    for (s2, y), g in d.groupby(['sic2', 'fy']):
        if len(g) < 20:
            continue
        ngroups += 1
        years.add(y)
    rows.append((nm, len(years), ngroups))
    cells_total += len(years)
    print(f'  {nm:20} years={len(years):3d}  groups(SIC2xyear>=20)={ngroups:4d}')
print(f'\nsignal-cycles (signal x fiscal-year cells) = {cells_total}')
print(f'signals screened = {len(rows)}')

# group-size distribution of the real ROA panel, to shape the synthetic control
d = P.copy(); d['s'] = SIGDEF['ROA'](d)
d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=['s'])
sizes = [len(g) for _, g in d.groupby(['sic2', 'fy']) if len(g) >= 20]
print(f'\nreal ROA groups: {len(sizes)}, sizes min={min(sizes)} median={int(np.median(sizes))} max={max(sizes)}')


# ---- the estimator, identical to edgar_lever1b.rho(ctrl=True) ---------------------------
def rho(gs, ctrl=True):
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
    return float(np.corrcoef(np.concatenate(a), np.concatenate(b))[0, 1])


def plant(c_a, c_x, rng):
    """Build synthetic groups with the real group-size distribution and a known answer."""
    gs = []
    for n in sizes:
        size = rng.standard_normal(n)                    # the observable (log assets)
        shock = rng.standard_normal(n)                   # the unobserved disturbance
        signal = 0.5 * size + shock                      # industry-adjusted value
        z = lambda v: (v - v.mean()) / (v.std() + 1e-9)
        latency_idx = -(c_a * z(shock) + c_x * z(size)) + 0.5 * rng.standard_normal(n)
        lat = rankdata(latency_idx).astype(float)
        gs.append((lat, signal - signal.mean(), size - size.mean()))
    return gs


print('\n=== Positive control: planted truth, identical size-partialled estimator ===')
rng = np.random.default_rng(SEED)
CASES = [('clean (c_a=0.0, c_x=0.3)', 0.0, 0.3, 'benign'),
         ('composition (c_a=0.0, c_x=2.0)', 0.0, 2.0, 'benign'),
         ('mild leak (c_a=0.3, c_x=0.7)', 0.3, 0.7, 'susceptible'),
         ('strong leak (c_a=1.0, c_x=0.7)', 1.0, 0.7, 'susceptible')]
ok = 0
print(f"{'planted case':34}{'rho_hat':>9}{'phi_req':>9}  {'screen says':12}{'should say':12}correct")
for label, c_a, c_x, expect in CASES:
    r = rho(plant(c_a, c_x, rng))
    phi = min(1.0, PHI_MIN + KAPPA * abs(r))
    says = 'susceptible' if abs(r) > RHO_THRESHOLD else 'benign'
    good = says == expect
    ok += good
    print(f'{label:34}{r:>+9.3f}{phi:>9.2f}  {says:12}{expect:12}{"yes" if good else "NO"}')
print(f'\nControl result: {ok}/{len(CASES)} correct.')
