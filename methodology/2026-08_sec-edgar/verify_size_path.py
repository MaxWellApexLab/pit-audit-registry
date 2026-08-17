"""verify_size_path.py — verify the two published numbers the shipped scripts do not print:
  corr(signal, log size)  within SIC2 x fiscal-year   [paper 5.7 says +0.51]
  size-mediated path = corr(lat,size) * corr(signal,size)  [paper 5.7 says -0.35]
Group construction is copied verbatim from edgar_lever1b.gbuild so the conventions match.
"""
import numpy as np, pandas as pd
from scipy.stats import rankdata

P = pd.read_parquet('edgar_panel.parquet')
P = P[P['Assets'] > 0].dropna(subset=['NetIncomeLoss', 'Assets', 'sic', 'filed', 'end']).copy()
P['roa'] = P['NetIncomeLoss'] / P['Assets']
P['filed'] = pd.to_datetime(P['filed']); P['end'] = pd.to_datetime(P['end'])
P['lat'] = (P['filed'] - P['end']).dt.days
P = P[(P['lat'] > 0) & (P['lat'] < 200)]
P['sic2'] = P['sic'].astype('Int64').astype(str).str.zfill(4).str[:2]
P['fy'] = P['end'].dt.year
P['logA'] = np.log(P['Assets'].clip(lower=1))

print(f'panel after filters: {len(P)} firm-years, {P.cik.nunique()} firms, '
      f'{P.sic2.nunique()} SIC2, {P.fy.min()}-{P.fy.max()}')

gs = []
for _, g in P.groupby(['sic2', 'fy']):
    if len(g) < 20:
        continue
    roa = g['roa'].clip(g['roa'].quantile(.02), g['roa'].quantile(.98)).values
    gs.append((rankdata(g['lat'].values).astype(float),      # latency rank
               roa - roa.mean(),                             # industry-adjusted signal
               g['logA'].values - g['logA'].mean()))         # demeaned log size
print(f'groups(SIC2 x year >= 20) = {len(gs)}')


def pooled_corr(pick_a, pick_b):
    a, b = [], []
    for lat, u, sz in gs:
        x, y = pick_a(lat, u, sz), pick_b(lat, u, sz)
        if x.std() < 1e-9 or y.std() < 1e-9:
            continue
        a.append((x - x.mean()) / x.std())
        b.append((y - y.mean()) / y.std())
    A, B = np.concatenate(a), np.concatenate(b)
    return np.corrcoef(A, B)[0, 1], len(A)


c_lat_size, n = pooled_corr(lambda l, u, s: l, lambda l, u, s: s)
c_sig_size, _ = pooled_corr(lambda l, u, s: u, lambda l, u, s: s)
c_lat_sig, _ = pooled_corr(lambda l, u, s: l, lambda l, u, s: u)

print(f'\npooled observations n = {n}')
print(f'corr(latency rank, log size)      = {c_lat_size:+.3f}   [paper: -0.69]')
print(f'corr(signal, log size)            = {c_sig_size:+.3f}   [paper: +0.51]')
print(f'corr(latency rank, signal) = raw  = {c_lat_sig:+.3f}   [paper: -0.30]')
print(f'size-mediated path = product      = {c_lat_size * c_sig_size:+.3f}   [paper: -0.35]')
