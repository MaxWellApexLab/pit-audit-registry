"""jkp_construction_control.py — positive control for a by-construction verdict.

The Global Factor Data documentation states one uniform release convention:

    "We assume that accounting variables are publically available 4 months after the end of
     the accounting period."                        -- Documentation.pdf, s6.2 General Information

A by-construction verdict claims that this convention closes the arrival-selection channel.
That claim is testable on planted-truth data even without access to arrival timestamps: build
one underlying cross-section, release it two ways, and run the identical estimator on both.

    policy "as-filed"    -> a value becomes usable on its own filing date (staggered by
                            filing SPEED, which depends on the unobserved disturbance)
    policy "uniform-4m"  -> a value becomes usable 4 months after its own period end, for
                            every firm alike (staggered only by FISCAL CALENDAR)

The third block is the boundary condition: the protection rests on fiscal year-end being
unrelated to the disturbance. Plant a violation and the screen fires again, under the same
uniform lag. That is the assumption the convention is actually buying.

Runs on numpy/scipy only. No JKP data is used or required -- this is a synthetic
demonstration of a mechanism, not a measurement of their dataset.
"""
import numpy as np
from scipy.stats import rankdata

SEED = 20260601
RHO_THRESHOLD = 0.10
PHI_MIN, KAPPA = 0.35, 1.0
N_FIRMS = 400          # firms per cross-section
N_COHORTS = 20         # independent cross-sections pooled
UNIFORM_LAG_DAYS = 122  # 4 months


def z(v):
    return (v - v.mean()) / (v.std() + 1e-9)


def build(policy, c_a, c_x, rng, fye_loads_on_shock=0.0):
    """One pooled set of cross-sections under a release policy."""
    gs = []
    for _ in range(N_COHORTS):
        n = N_FIRMS
        size = rng.standard_normal(n)                     # observable (log market equity)
        shock = rng.standard_normal(n)                    # unobserved disturbance
        signal = 0.5 * size + shock                       # the accounting characteristic

        # fiscal year-end, spread over the 12 months of the year.
        # Monotone rank mapping, NOT a wrapped shift: wrapping at 365 would destroy the very
        # ordering the adversarial case is supposed to plant.
        if fye_loads_on_shock:
            # adversarial: fiscal year-end ordering tracks the unobserved shock
            idx = fye_loads_on_shock * z(shock) + rng.standard_normal(n)
            fye_day = 365.0 * rankdata(idx) / n
        else:
            fye_day = rng.uniform(0.0, 365.0, n)

        # how fast the firm actually files, in days after its own period end
        file_lag = 60 + 40 * (-(c_a * z(shock) + c_x * z(size)) + 0.5 * rng.standard_normal(n))

        if policy == 'as-filed':
            usable = fye_day + file_lag
        elif policy == 'uniform-4m':
            usable = fye_day + UNIFORM_LAG_DAYS       # identical offset for every firm
        else:
            raise ValueError(policy)

        latency = rankdata(usable).astype(float)
        gs.append((latency, signal - signal.mean(), size - size.mean()))
    return gs


def rho(gs):
    """Partial corr(arrival latency, complete-cross-section residual | size), pooled."""
    a, b = [], []
    for lat, u, sz in gs:
        X = np.column_stack([np.ones(len(lat)), sz])
        l = lat - X @ np.linalg.lstsq(X, lat, rcond=None)[0]
        uu = u - X @ np.linalg.lstsq(X, u, rcond=None)[0]
        if l.std() < 1e-9 or uu.std() < 1e-9:
            continue
        a.append(z(l))
        b.append(z(uu))
    if not a:
        return 0.0
    return float(np.corrcoef(np.concatenate(a), np.concatenate(b))[0, 1])


CASES = [
    # (release policy, c_a, c_x, fye_loads_on_shock, label, expected)
    ('as-filed',   0.0, 0.3, 0.0, 'clean, no selection on the disturbance',      'benign'),
    ('as-filed',   0.0, 2.0, 0.0, 'composition: filing speed set by SIZE, hard', 'benign'),
    ('as-filed',   0.3, 0.7, 0.0, 'mild leak: filing speed sees the shock',      'susceptible'),
    ('as-filed',   1.0, 0.7, 0.0, 'strong leak: filing speed sees the shock',    'susceptible'),
    ('uniform-4m', 0.3, 0.7, 0.0, 'SAME mild leak, uniform 4-month release',     'benign'),
    ('uniform-4m', 1.0, 0.7, 0.0, 'SAME strong leak, uniform 4-month release',   'benign'),
    ('uniform-4m', 1.0, 0.7, 1.0, 'uniform lag BUT fiscal year-end tracks shock', 'susceptible'),
]

if __name__ == '__main__':
    rng = np.random.default_rng(SEED)
    print(f'threshold |rho_hat| > {RHO_THRESHOLD}; phi_req = min(1, {PHI_MIN} + {KAPPA}*|rho_hat|)')
    print(f'{N_COHORTS} cross-sections x {N_FIRMS} firms per case\n')
    print(f"{'release policy':13}{'c_a':>5}{'c_x':>5}  {'planted case':46}"
          f"{'rho_hat':>9}{'phi_req':>9}  {'screen says':13}{'should say':13}correct")
    ok = 0
    for policy, c_a, c_x, fye, label, expect in CASES:
        r = rho(build(policy, c_a, c_x, rng, fye))
        phi = min(1.0, PHI_MIN + KAPPA * abs(r))
        says = 'susceptible' if abs(r) > RHO_THRESHOLD else 'benign'
        good = says == expect
        ok += good
        print(f'{policy:13}{c_a:>5.1f}{c_x:>5.1f}  {label:46}'
              f'{r:>+9.3f}{phi:>9.2f}  {says:13}{expect:13}{"yes" if good else "NO"}')
    print(f'\nControl result: {ok}/{len(CASES)} correct.')
    print('\nRows 3-4 vs 5-6 are the whole argument: the SAME planted leakage that the screen')
    print('detects under as-filed release becomes undetectable under a uniform 4-month release,')
    print('because filing speed no longer orders arrival. Row 7 is the boundary condition.')
