#!/usr/bin/env python3
"""
World Bank macro dashboard builder: India vs Indonesia vs Brazil vs South Africa.

Usage:   pip install requests pandas openpyxl
         python build_macro_project.py

Pulls live data from the World Bank Indicators API (no key needed) and writes:
  macro_dashboard.xlsx      Excel workbook: data, analysis tabs, native charts
  macro_dashboard.html      interactive dashboard (open in any browser)
  worldbank_long.csv        tidy data for Power BI (Get Data > Text/CSV)
  findings_summary.md       key computed results (tables) for the analytical brief
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COUNTRIES = {"IND": "India", "IDN": "Indonesia", "BRA": "Brazil", "ZAF": "South Africa"}
START, END = 2000, 2024
PRE = (2015, 2019)    # baseline window
POST = (2021, 2024)   # comparison window (2020 COVID shock year excluded)

# key: (WB code, label, direction: +1 higher=better, -1 higher=worse, 0 neutral)
INDICATORS = {
    "gdp_growth":      ("NY.GDP.MKTP.KD.ZG", "GDP growth (annual %)", +1),
    "inflation":       ("FP.CPI.TOTL.ZG", "Inflation, CPI (annual %)", -1),
    "gov_debt":        ("GGXWDG_NGDP", "General govt gross debt (% of GDP, IMF WEO via FRED)", -1),
    "gov_debt_central": ("GC.DOD.TOTL.GD.ZS", "Central govt debt (% of GDP, World Bank; patchy)", 0),
    "exports_gdp":     ("NE.EXP.GNFS.ZS", "Exports (% of GDP)", 0),
    "imports_gdp":     ("NE.IMP.GNFS.ZS", "Imports (% of GDP)", 0),
    "fdi":             ("BX.KLT.DINV.WD.GD.ZS", "FDI net inflows (% of GDP)", +1),
    "current_account": ("BN.CAB.XOKA.GD.ZS", "Current account balance (% of GDP)", +1),
    "unemployment":    ("SL.UEM.TOTL.ZS", "Unemployment (% labour force, ILO modelled)", -1),
    "fx_rate":         ("PA.NUS.FCRF", "Exchange rate (LCU per USD, period avg)", 0),
    "real_rate":       ("FR.INR.RINR", "Real interest rate (%)", 0),
    "lending_rate":    ("FR.INR.LEND", "Lending interest rate (%)", 0),
    "reserves_months": ("FI.RES.TOTL.MO", "Reserves (months of imports)", +1),
}
DERIVED = {
    "trade_balance": ("Trade balance (% of GDP) = exports - imports", +1),
    "fx_change":     ("Currency depreciation vs USD (% y/y, + = weaker)", -1),
}
LABELS = {k: v[1] for k, v in INDICATORS.items()}
LABELS.update({k: v[0] for k, v in DERIVED.items()})
SCORE_KEYS = ["gdp_growth", "inflation", "gov_debt", "trade_balance", "fdi",
              "current_account", "unemployment", "fx_change", "reserves_months"]
DIRECTION = {k: v[2] for k, v in INDICATORS.items()}
DIRECTION.update({k: v[1] for k, v in DERIVED.items()})

# vulnerability screens: (name, test)
FLAGS = {
    "Inflation >10%":           lambda r: r.inflation > 10,
    "GDP contraction":          lambda r: r.gdp_growth < 0,
    "Current a/c deficit >3%":  lambda r: r.current_account < -3,
    "Govt debt >60% GDP":       lambda r: r.gov_debt > 60,
    "Reserves <3 months":       lambda r: r.reserves_months < 3,
    "Unemployment >10%":        lambda r: r.unemployment > 10,
    "Currency fell >15% y/y":   lambda r: r.fx_change > 15,
}


def fetch_indicator(code):
    import requests
    url = f"https://api.worldbank.org/v2/country/{';'.join(COUNTRIES)}/indicator/{code}"
    rows, page = [], 1
    while True:
        r = requests.get(url, params={"format": "json", "date": f"{START}:{END}",
                                      "per_page": 1000, "page": page}, timeout=60)
        r.raise_for_status()
        j = r.json()
        if len(j) < 2 or j[1] is None:
            break
        rows += j[1]
        if page >= int(j[0]["pages"]):
            break
        page += 1
    return [(x["countryiso3code"], int(x["date"]), x["value"])
            for x in rows if x["value"] is not None]


# IMF WEO (Apr 2025 vintage) general govt gross debt, % of GDP, 2000-2024, as published on FRED
# (series GGGDTA/GGGDTP + IN/ID/BR/ZA + A188N). Embedded so the project still builds if the live download is blocked.
IMF_DEBT_EMBEDDED = {
    "IND": [74.941, 80.110, 84.304, 85.883, 84.890, 82.378, 77.941, 75.455, 74.368, 72.770, 67.702, 68.648, 67.985,
            67.713, 67.102, 69.049, 68.943, 69.669, 70.392, 75.040, 88.427, 83.487, 82.173, 81.231, 81.286],
    "IDN": [87.437, 73.702, 62.339, 55.643, 51.328, 42.612, 35.848, 38.121, 30.252, 26.483, 26.363, 23.106, 22.955,
            24.884, 24.645, 27.013, 27.955, 29.396, 30.423, 30.563, 39.747, 41.140, 40.141, 39.601, 40.189],
    "BRA": [62.198, 67.331, 76.095, 71.514, 68.025, 66.969, 64.599, 63.025, 61.420, 64.702, 62.433, 60.634, 61.614,
            59.595, 61.617, 71.730, 77.422, 82.745, 84.777, 87.118, 96.007, 88.934, 83.939, 84.001, 87.284],
    "ZAF": [37.929, 38.045, 31.801, 31.514, 30.733, 29.637, 28.030, 24.326, 24.045, 26.995, 31.185, 34.742, 37.408,
            40.356, 43.253, 45.195, 47.134, 48.588, 51.536, 56.101, 68.927, 68.672, 70.832, 73.363, 76.356],
}


def embedded_debt():
    return [(iso, 2000 + i, v) for iso, vals in IMF_DEBT_EMBEDDED.items()
            for i, v in enumerate(vals) if START <= 2000 + i <= END]


FRED_DEBT = {"IND": "IN", "IDN": "ID", "BRA": "BR", "ZAF": "ZA"}   # IMF WEO series mirrored on FRED


def fetch_fred_debt():
    """IMF WEO general govt gross debt (% GDP) via FRED: actual series + projection series."""
    import io
    import requests
    out = []
    for iso, cc in FRED_DEBT.items():
        seen = {}
        for prefix in ("GGGDTA", "GGGDTP"):          # A = actuals, P = projections/estimates
            sid = f"{prefix}{cc}A188N"
            try:
                r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": sid},
                                 timeout=20, headers={"User-Agent": "Mozilla/5.0"})
                r.raise_for_status()
            except Exception:
                if prefix == "GGGDTA":
                    raise                              # actuals are required, projections optional
                continue
            df = pd.read_csv(io.StringIO(r.text))
            df.columns = ["date", "v"]
            df["v"] = pd.to_numeric(df["v"], errors="coerce")
            for d, v in zip(df["date"], df["v"]):
                y = int(str(d)[:4])
                if pd.notna(v) and START <= y <= END and y not in seen:
                    seen[y] = float(v)
        out += [(iso, y, v) for y, v in seen.items()]
    return out


def with_retry(fn, *args, tries=3):
    import time
    for i in range(tries):
        try:
            return fn(*args)
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"    retrying ({e.__class__.__name__})...")
            time.sleep(2 * (i + 1))


def fetch_all():
    recs = []
    for key, (code, label, _) in INDICATORS.items():
        try:
            if key == "gov_debt":
                data = []
                for name, fn, args in [("IMF WEO via FRED (live)", fetch_fred_debt, ()),
                                       ("IMF WEO Apr 2025 via FRED (embedded copy)", embedded_debt, ()),
                                       ("World Bank central govt (patchy)", fetch_indicator, ("GC.DOD.TOTL.GD.ZS",))]:
                    try:
                        d = with_retry(fn, *args, tries=1)
                        if len({x[0] for x in d}) == len(COUNTRIES) and len(d) >= 60:
                            data = d
                            print(f"  (gov debt source: {name})")
                            break
                        print(f"  ! {name}: incomplete ({len(d)} obs), trying next source")
                    except Exception as e:
                        print(f"  ! {name} failed ({e.__class__.__name__}), trying next source")
            else:
                data = with_retry(fetch_indicator, code)
        except Exception as e:  # keep going if one series fails
            print(f"  !!! {code} FAILED: {e}  -> re-run the script")
            data = []
        print(f"  {code:22s} {len(data):3d} obs")
        for iso, yr, val in data:
            recs.append(dict(iso3=iso, country=COUNTRIES[iso], year=yr, key=key,
                             indicator=label, code=code, value=val))
    if not recs:
        sys.exit("No data returned. Check your internet connection.")
    return pd.DataFrame(recs)


def make_panel(long_df):
    p = long_df.pivot_table(index=["country", "year"], columns="key", values="value").reset_index()
    for k in INDICATORS:
        if k not in p:
            p[k] = np.nan
    p = p.sort_values(["country", "year"])
    p["trade_balance"] = p.exports_gdp - p.imports_gdp
    p["fx_change"] = p.groupby("country").fx_rate.pct_change(fill_method=None) * 100
    return p


def win(p, w):
    return p[(p.year >= w[0]) & (p.year <= w[1])]


def analyse(p):
    out = {}
    # z-scores on the pooled panel, signed so that higher = better
    z = p[["country", "year"]].copy()
    for k in SCORE_KEYS:
        s = p[k]
        z[k] = DIRECTION[k] * (s - s.mean()) / s.std()
    pre = win(z, PRE).groupby("country")[SCORE_KEYS].mean()
    post = win(z, POST).groupby("country")[SCORE_KEYS].mean()
    chg = (post - pre)                       # negative = deterioration
    chg["COMPOSITE"] = chg.mean(axis=1, skipna=True)
    out["deterioration"] = chg.round(2).reset_index()

    raw_pre = win(p, PRE).groupby("country")[SCORE_KEYS].mean()
    raw_post = win(p, POST).groupby("country")[SCORE_KEYS].mean()
    out["levels"] = pd.concat({f"{PRE[0]}-{PRE[1]} avg": raw_pre,
                               f"{POST[0]}-{POST[1]} avg": raw_post}, axis=1).round(2)
    out["levels"].columns = [f"{a} | {b}" for a, b in out["levels"].columns]
    out["levels"] = out["levels"].reset_index()

    # inflation vs growth co-movement
    rows = []
    for c, g in p.groupby("country"):
        g = g.set_index("year")
        ex = g.drop(index=2020, errors="ignore")
        rows.append(dict(country=c,
                         corr_same_year=g.inflation.corr(g.gdp_growth),
                         corr_ex_2020=ex.inflation.corr(ex.gdp_growth),
                         corr_infl_lead_1y=g.inflation.shift(1).corr(g.gdp_growth),
                         n=int(g[["inflation", "gdp_growth"]].dropna().shape[0])))
    rows.append(dict(country="POOLED", corr_same_year=p.inflation.corr(p.gdp_growth),
                     corr_ex_2020=p[p.year != 2020].inflation.corr(p[p.year != 2020].gdp_growth),
                     corr_infl_lead_1y=np.nan, n=int(p[["inflation", "gdp_growth"]].dropna().shape[0])))
    out["correlation"] = pd.DataFrame(rows).round(2)

    # external-sector scorecard, last 10 years
    ext = p[p.year >= END - 9].groupby("country").agg(
        current_account_avg=("current_account", "mean"),
        current_account_vol=("current_account", "std"),
        fdi_avg=("fdi", "mean"),
        trade_balance_avg=("trade_balance", "mean"),
        reserves_months_avg=("reserves_months", "mean"),
        exports_gdp_avg=("exports_gdp", "mean"),
        avg_depreciation_pa=("fx_change", "mean"))
    rk = pd.DataFrame({
        "current_account_avg": ext.current_account_avg.rank(ascending=False),
        "current_account_vol": ext.current_account_vol.rank(ascending=True),
        "fdi_avg": ext.fdi_avg.rank(ascending=False),
        "trade_balance_avg": ext.trade_balance_avg.rank(ascending=False),
        "reserves_months_avg": ext.reserves_months_avg.rank(ascending=False),
        "avg_depreciation_pa": ext.avg_depreciation_pa.rank(ascending=True)})
    ext["avg_rank (1=best)"] = rk.mean(axis=1)
    out["external"] = ext.round(2).sort_values("avg_rank (1=best)").reset_index()

    # vulnerability flags
    fl = []
    for r in p.itertuples():
        hit = []
        for name, fn in FLAGS.items():
            try:
                if fn(r):
                    hit.append(name)
            except Exception:
                pass
        fl.append(dict(country=r.country, year=r.year, n_flags=len(hit), flags="; ".join(hit)))
    fl = pd.DataFrame(fl)
    out["flags"] = fl
    recent = fl[fl.year >= END - 9]
    out["flag_summary"] = (recent.groupby("country").n_flags.agg(["mean", "max", "sum"])
                           .round(2).rename(columns={"mean": "avg_flags_per_yr", "max": "worst_year_flags",
                                                     "sum": "total_flags"}).reset_index())
    # data coverage so gaps are visible
    cov = p.groupby("country")[list(INDICATORS) + list(DERIVED)].count()
    out["coverage"] = cov.reset_index()
    return out


def write_excel(path, long_df, p, res):
    from openpyxl.chart import LineChart, Reference
    from openpyxl.styles import Font, PatternFill
    readme = pd.DataFrame({"Notes": [
        "World Bank macro dashboard: India, Indonesia, Brazil, South Africa",
        f"Source: World Bank Open Data (WDI) via Indicators API, {START}-{END}. Pulled at build time.",
        "Sheets: Panel (wide data), Data_Long (tidy, for Power BI), Deterioration, Levels, Correlation, "
        "External, Vulnerability, Flag_Summary, Coverage, Charts.",
        f"Deterioration = change in signed z-score, {PRE[0]}-{PRE[1]} avg to {POST[0]}-{POST[1]} avg "
        "(2020 excluded). Z-scores use the pooled country-year panel; sign flipped so higher = better. "
        "Negative composite = worse conditions.",
        "Gov debt = IMF WEO general government gross debt (% GDP), pulled from FRED (actuals + latest-year estimate; see console message for source used). "
        "gov_debt_central is the patchy World Bank central-govt series, kept for reference only.",
        "Unemployment is ILO modelled estimate, not national survey headline.",
        "Interest rates: WB real and lending rates. For policy rates use central bank / IMF IFS.",
        "Vulnerability thresholds are rules of thumb (see Vulnerability sheet), not forecasts."]})
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        readme.to_excel(xw, sheet_name="README", index=False)
        p.round(3).to_excel(xw, sheet_name="Panel", index=False)
        long_df.to_excel(xw, sheet_name="Data_Long", index=False)
        res["deterioration"].to_excel(xw, sheet_name="Deterioration", index=False)
        res["levels"].to_excel(xw, sheet_name="Levels", index=False)
        res["correlation"].to_excel(xw, sheet_name="Correlation", index=False)
        res["external"].to_excel(xw, sheet_name="External", index=False)
        res["flags"].to_excel(xw, sheet_name="Vulnerability", index=False)
        res["flag_summary"].to_excel(xw, sheet_name="Flag_Summary", index=False)
        res["coverage"].to_excel(xw, sheet_name="Coverage", index=False)
        wb = xw.book
        for ws in wb.worksheets:
            ws.freeze_panes = "A2"
            for c in ws[1]:
                c.font = Font(bold=True, color="FFFFFF")
                c.fill = PatternFill("solid", fgColor="1F3864")
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 18
        wb["README"].column_dimensions["A"].width = 140
        wb["Panel"].auto_filter.ref = wb["Panel"].dimensions

        cs = wb.create_sheet("Charts")
        countries = list(COUNTRIES.values())
        years = sorted(p.year.unique())
        chart_keys = ["gdp_growth", "inflation", "gov_debt", "current_account", "fdi",
                      "unemployment", "fx_change", "reserves_months"]
        row = 1
        for i, k in enumerate(chart_keys):
            cs.cell(row, 1, LABELS[k]).font = Font(bold=True)
            cs.cell(row + 1, 1, "Year")
            for j, c in enumerate(countries):
                cs.cell(row + 1, 2 + j, c)
            for r_i, y in enumerate(years):
                cs.cell(row + 2 + r_i, 1, int(y))
                for j, c in enumerate(countries):
                    v = p[(p.country == c) & (p.year == y)][k]
                    v = v.iloc[0] if len(v) else np.nan
                    if pd.notna(v):
                        cs.cell(row + 2 + r_i, 2 + j, round(float(v), 3))
            ch = LineChart()
            ch.title, ch.height, ch.width = LABELS[k], 7.5, 15
            n = len(years)
            ch.add_data(Reference(cs, min_col=2, max_col=1 + len(countries), min_row=row + 1, max_row=row + 1 + n),
                        titles_from_data=True)
            ch.set_categories(Reference(cs, min_col=1, min_row=row + 2, max_row=row + 1 + n))
            cs.add_chart(ch, f"H{1 + (i * 17)}")
            row += n + 4
    print(f"  wrote {path}")


HTML = r"""<!doctype html><html><head><meta charset="utf-8"><title>Macro Dashboard</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
body{font-family:system-ui,Arial;margin:0;background:#f4f6f9;color:#1b2430}
header{background:#1f3864;color:#fff;padding:14px 22px}h1{margin:0;font-size:20px}
header small{opacity:.8}
.bar{display:flex;flex-wrap:wrap;gap:18px;align-items:center;padding:12px 22px;background:#fff;border-bottom:1px solid #dde}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:16px;padding:16px 22px}
.card{background:#fff;border-radius:8px;padding:14px;box-shadow:0 1px 3px #0002}
.card h3{margin:0 0 8px;font-size:15px}table{border-collapse:collapse;width:100%;font-size:12px}
td,th{padding:4px 6px;border:1px solid #e3e6ea;text-align:center}th{background:#eef1f6}
label{font-size:13px;margin-right:8px;cursor:pointer}select,input{font-size:13px}
.note{font-size:12px;color:#556;margin-top:6px}
</style></head><body>
<header><h1>Macro Dashboard: India | Indonesia | Brazil | South Africa</h1>
<small>Source: World Bank Open Data (WDI). Built __STAMP__</small></header>
<div class="bar"><div>Indicator <select id="ind"></select></div><div id="cs"></div>
<div>Years <input type="number" id="y0" style="width:64px"> to <input type="number" id="y1" style="width:64px"></div></div>
<div class="grid">
<div class="card" style="grid-column:1/-1"><h3 id="t1"></h3><canvas id="c1" height="90"></canvas></div>
<div class="card"><h3>Inflation vs GDP growth (each dot = country-year)</h3><canvas id="c2"></canvas>
<div class="note" id="corr"></div></div>
<div class="card"><h3>Macro deterioration: change in composite z-score (negative = worse)</h3><canvas id="c3"></canvas>
<div class="note">Baseline __PRE__ vs __POST__ average; 9 indicators, pooled z-scores, higher = better.</div></div>
<div class="card" style="grid-column:1/-1"><h3>Vulnerability heatmap: number of stress flags per year</h3><div id="hm"></div>
<div class="note">Flags: inflation&gt;10%, GDP contraction, current account deficit&gt;3% GDP, general govt gross debt&gt;60% GDP, reserves&lt;3 months imports, unemployment&gt;10%, currency down&gt;15% y/y. Hover for detail. Blank = no data.</div></div>
<div class="card" style="grid-column:1/-1"><h3>External-sector scorecard (last 10 years, sorted best to worst)</h3><div id="ext"></div></div>
</div>
<script>
const D=__DATA__;const COL={India:'#e07b00',Indonesia:'#c0392b',Brazil:'#27ae60','South Africa':'#2c6fbb'};
const cs=Object.keys(COL);const yrs=D.panel.map(r=>r.year);const ymin=Math.min(...yrs),ymax=Math.max(...yrs);
const sel=document.getElementById('ind');
Object.entries(D.labels).forEach(([k,v])=>{const o=document.createElement('option');o.value=k;o.textContent=v;sel.appendChild(o)});
const y0=document.getElementById('y0'),y1=document.getElementById('y1');y0.value=ymin;y1.value=ymax;
const box=document.getElementById('cs');
cs.forEach(c=>{box.insertAdjacentHTML('beforeend',`<label><input type="checkbox" checked value="${c}"> <span style="color:${COL[c]}">&#9632;</span> ${c}</label>`)});
const on=()=>[...box.querySelectorAll('input:checked')].map(i=>i.value);
const rng=()=>[+y0.value,+y1.value];
let c1,c2,c3;
function draw(){
 const [a,b]=rng(),k=sel.value,act=on();
 const ys=[];for(let y=a;y<=b;y++)ys.push(y);
 document.getElementById('t1').textContent=D.labels[k];
 const ds=act.map(c=>({label:c,borderColor:COL[c],backgroundColor:COL[c],tension:.2,spanGaps:false,
  data:ys.map(y=>{const r=D.panel.find(r=>r.country==c&&r.year==y);return r&&r[k]!=null?r[k]:null})}));
 if(c1)c1.destroy();c1=new Chart('c1',{type:'line',data:{labels:ys,datasets:ds},options:{interaction:{mode:'index',intersect:false}}});
 const sc=act.map(c=>({label:c,backgroundColor:COL[c],data:D.panel.filter(r=>r.country==c&&r.year>=a&&r.year<=b&&r.inflation!=null&&r.gdp_growth!=null).map(r=>({x:r.inflation,y:r.gdp_growth,year:r.year}))}));
 if(c2)c2.destroy();c2=new Chart('c2',{type:'scatter',data:{datasets:sc},options:{scales:{x:{title:{display:true,text:'Inflation %'}},y:{title:{display:true,text:'GDP growth %'}}},
  plugins:{tooltip:{callbacks:{label:t=>`${t.dataset.label} ${t.raw.year}: infl ${t.raw.x.toFixed(1)}, growth ${t.raw.y.toFixed(1)}`}}}}});
 document.getElementById('corr').innerHTML='Correlation (whole sample): '+D.corr.map(r=>`${r.country} <b>${r.corr_same_year}</b> (ex-2020 ${r.corr_ex_2020})`).join(' | ');
 // heatmap
 const hy=ys;let h='<table><tr><th></th>'+hy.map(y=>`<th>${y}</th>`).join('')+'</tr>';
 act.forEach(c=>{h+=`<tr><th>${c}</th>`+hy.map(y=>{const f=D.flags.find(r=>r.country==c&&r.year==y);
  if(!f)return'<td></td>';const n=f.n_flags,bg=n==0?'#e8f5e9':n==1?'#fff3cd':n==2?'#ffd8a8':'#f5a3a3';
  return`<td style="background:${bg}" title="${f.flags||'none'}">${n}</td>`}).join('')+'</tr>'});
 document.getElementById('hm').innerHTML=h+'</table>';
}
function tbl(rows){if(!rows.length)return'';const ks=Object.keys(rows[0]);
 return'<table><tr>'+ks.map(k=>`<th>${k}</th>`).join('')+'</tr>'+rows.map(r=>'<tr>'+ks.map(k=>`<td>${r[k]==null?'':r[k]}</td>`).join('')+'</tr>').join('')+'</table>'}
document.getElementById('ext').innerHTML=tbl(D.ext);
c3=new Chart('c3',{type:'bar',data:{labels:D.det.map(r=>r.country),datasets:[{label:'Composite change',data:D.det.map(r=>r.COMPOSITE),backgroundColor:D.det.map(r=>COL[r.country])}]},options:{plugins:{legend:{display:false}}}});
[sel,y0,y1].forEach(e=>e.addEventListener('change',draw));box.addEventListener('change',draw);draw();
</script></body></html>"""


def clean(df):
    return json.loads(df.replace({np.nan: None}).to_json(orient="records"))


def write_html(path, p, res):
    data = dict(
        labels={k: LABELS[k] for k in list(INDICATORS) + list(DERIVED)},
        panel=clean(p.round(3)), flags=clean(res["flags"]),
        det=clean(res["deterioration"]), ext=clean(res["external"]),
        corr=clean(res["correlation"][res["correlation"].country != "POOLED"]))
    html = (HTML.replace("__DATA__", json.dumps(data))
            .replace("__STAMP__", pd.Timestamp.now().strftime("%d %b %Y"))
            .replace("__PRE__", f"{PRE[0]}-{PRE[1]}").replace("__POST__", f"{POST[0]}-{POST[1]}"))
    Path(path).write_text(html, encoding="utf-8")
    print(f"  wrote {path}")


def write_findings(path, res):
    parts = [f"# Findings summary (World Bank WDI, {START}-{END})\n",
             f"Baseline {PRE[0]}-{PRE[1]} vs comparison {POST[0]}-{POST[1]}; negative z-change = deterioration.\n"]
    for title, key in [("Deterioration (signed z change)", "deterioration"),
                       ("Average levels", "levels"),
                       ("Inflation vs growth correlation", "correlation"),
                       ("External-sector scorecard", "external"),
                       ("Vulnerability flags (last 10 yrs)", "flag_summary"),
                       ("Data coverage (obs count per series)", "coverage")]:
        parts.append(f"\n## {title}\n```\n{res[key].to_string(index=False)}\n```")
    f = res["flags"]
    parts.append("\n## Flags by country-year (last 6 years)\n```\n" +
                 f[f.year >= END - 5].to_string(index=False) + "\n```")
    Path(path).write_text("\n".join(parts), encoding="utf-8")
    print(f"  wrote {path}")


def main(long_df=None, outdir="."):
    out = Path(outdir)
    if long_df is None:
        print("Fetching from World Bank API...")
        long_df = fetch_all()
    p = make_panel(long_df)
    res = analyse(p)
    long_df.to_csv(out / "worldbank_long.csv", index=False)
    write_excel(out / "macro_dashboard.xlsx", long_df, p, res)
    write_html(out / "macro_dashboard.html", p, res)
    write_findings(out / "findings_summary.md", res)
    print("\nDone. Outputs: macro_dashboard.xlsx, macro_dashboard.html, worldbank_long.csv, findings_summary.md")


if __name__ == "__main__":
    main()
