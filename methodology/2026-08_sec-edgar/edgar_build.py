"""
edgar_build.py — build a reusable REAL US as-filed panel from free SEC APIs.
Per sampled firm: companyfacts (us-gaap concepts, earliest-filed 10-K per fiscal-period
end, so the filing date is the ORIGINAL annual report = observed announcement) + submissions
(SIC industry). Saves edgar_panel.parquet for downstream levers (rho_hat,
matched excess, out-of-sample, factor-zoo susceptibility map).
"""
import json, urllib.request, urllib.error, time, sys
import numpy as np, pandas as pd
# SEC asks every caller to identify themselves. Put YOUR name and address here
# before running; the endpoints throttle or refuse anonymous traffic.
UA={'User-Agent':'YOUR NAME your.address@example.org'}
N_SAMPLE=900; SLEEP=0.11
OUT='edgar_panel.parquet'

FLOWS=['NetIncomeLoss','Revenues','RevenueFromContractWithCustomerExcludingAssessedTax',
       'SalesRevenueNet','GrossProfit','OperatingIncomeLoss',
       'NetCashProvidedByUsedInOperatingActivities','ResearchAndDevelopmentExpense']
STOCKS=['Assets','StockholdersEquity','InventoryNet','PropertyPlantAndEquipmentNet',
        'Liabilities','AssetsCurrent','LiabilitiesCurrent','CashAndCashEquivalentsAtCarryingValue']

def get(url, tries=3):
    for _ in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code==404: return None
            time.sleep(0.6)
        except Exception: time.sleep(0.6)
    return None

def earliest(units, fy_only):
    best={}
    for u in units:
        if u.get('form')!='10-K' or not u.get('filed'): continue
        if fy_only and u.get('fp')!='FY': continue
        e=u['end']; f=u['filed']
        if e not in best or f<best[e][1]: best[e]=(u['val'],f)
    return best

def firm_rows(cik, sic):
    cf=get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json')
    if not cf: return []
    g=cf.get('facts',{}).get('us-gaap',{})
    def ser(tag,fy):
        return earliest(g.get(tag,{}).get('units',{}).get('USD',[]), fy)
    flows={t:ser(t,True) for t in FLOWS}; stocks={t:ser(t,False) for t in STOCKS}
    ends=set();
    for d in list(flows.values())+list(stocks.values()): ends|=set(d.keys())
    rows=[]
    for e in ends:
        rec={'cik':cik,'sic':sic,'end':e}
        filed=None
        for t in FLOWS:
            if e in flows[t]: rec[t]=flows[t][e][0]; filed=filed or flows[t][e][1]
        for t in STOCKS:
            if e in stocks[t]: rec[t]=stocks[t][e][0]; filed=filed or stocks[t][e][1]
        if 'Assets' in rec and filed: rec['filed']=filed; rows.append(rec)
    return rows

def main():
    fr=get('https://data.sec.gov/api/xbrl/frames/us-gaap/Assets/USD/CY2015Q4I.json')
    ciks=[r['cik'] for r in fr['data']]; rng=np.random.default_rng(11); rng.shuffle(ciks)
    ciks=ciks[:N_SAMPLE]
    print(f'building panel from {len(ciks)} firms',flush=True)
    rows=[]; ok=0
    for j,c in enumerate(ciks):
        sub=get(f'https://data.sec.gov/submissions/CIK{c:010d}.json')
        sic=sub.get('sic') if sub else None
        r=firm_rows(c, sic)
        if r: ok+=1; rows+=r
        time.sleep(SLEEP)
        if (j+1)%100==0: print(f'  {j+1}/{len(ciks)} firms, {ok} usable, {len(rows)} firm-years',flush=True)
    P=pd.DataFrame(rows)
    P.to_parquet(OUT)
    print(f'saved {OUT}: {len(P)} firm-years, {P.cik.nunique()} firms, {P.sic.notna().sum()} with SIC',flush=True)
    print('columns:', [c for c in P.columns],flush=True)

if __name__=='__main__': main()
