from datetime import datetime
import io, json, os, re, sqlite3, logging
import numpy as np
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objects as go
import requests
from flask import (Flask, Response, abort, flash, jsonify, redirect, render_template,
                   request, url_for)
import config

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
logging.basicConfig(level=logging.INFO)

# ---------- database (path configurable so it can live on a persistent volume) ----------
os.makedirs(config.DATA_DIR, exist_ok=True)
DB = os.path.join(config.DATA_DIR, "reports.db")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS reports (id INTEGER PRIMARY KEY AUTOINCREMENT,
            district TEXT, issue_type TEXT, description TEXT, report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, email TEXT, subject TEXT, message TEXT, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
init_db()

# ---------- data ----------
CH = {"Digital_App_Pct": "Digital finance", "Bank_Loan_Pct": "Bank loans", "Saving_Group_Pct": "Saving groups"}
COLS = list(CH)
TEAL, AMBER, RED, GREEN, GREY = "#0b7a75", "#f2b134", "#c0392b", "#2e9e5b", "#c9d3d1"
CENTROIDS = {"Nyarugenge": (-1.95, 30.06), "Gasabo": (-1.88, 30.12), "Kicukiro": (-1.99, 30.10), "Nyagatare": (-1.30, 30.33),
    "Gatsibo": (-1.58, 30.43), "Kayonza": (-1.88, 30.64), "Kirehe": (-2.23, 30.71), "Ngoma": (-2.17, 30.50),
    "Bugesera": (-2.22, 30.15), "Rwamagana": (-1.95, 30.43), "Nyanza": (-2.35, 29.75), "Gisagara": (-2.62, 29.85),
    "Nyaruguru": (-2.75, 29.55), "Huye": (-2.60, 29.74), "Nyamagabe": (-2.47, 29.43), "Ruhango": (-2.23, 29.78),
    "Muhanga": (-2.08, 29.75), "Kamonyi": (-2.00, 29.89), "Karongi": (-2.10, 29.37), "Rutsiro": (-1.95, 29.33),
    "Rubavu": (-1.70, 29.30), "Nyabihu": (-1.65, 29.50), "Ngororero": (-1.86, 29.60), "Rusizi": (-2.50, 29.00),
    "Nyamasheke": (-2.33, 29.15), "Rulindo": (-1.73, 29.99), "Gakenke": (-1.70, 29.78), "Musanze": (-1.50, 29.63),
    "Burera": (-1.46, 29.83), "Gicumbi": (-1.60, 30.07)}

def load_df():
    p = os.path.join(BASE, "data", "Rwanda_Poverty_Finance_Data.csv")
    d = pd.read_csv(p)
    d = d.dropna(subset=["District"]).drop_duplicates("District").fillna(0)
    d["Total_Reach"] = d[COLS].sum(axis=1)
    mm = lambda s: (s - s.min()) / ((s.max() - s.min()) or 1)
    # Exclusion Priority Index (0-100): half poverty, half lack of financial-service reach
    d["Priority"] = (50 * mm(d["Poverty_Rate_Pct"]) + 50 * (1 - mm(d["Total_Reach"]))).round(1)
    d["Rank"] = d["Priority"].rank(ascending=False, method="min").astype(int)
    return d.sort_values("District").reset_index(drop=True)
df = load_df()
DISTRICTS = df["District"].tolist()

GEO_FILE = os.path.join(BASE, "static", "data", "rwanda_districts.geojson")
GEO_URL = ("https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/9469f09592ced973a3448cf66b6100b741b64c0d/"
           "releaseData/gbOpen/RWA/ADM2/geoBoundaries-RWA-ADM2_simplified.geojson")
_geo = None
def get_geo():
    """Boundaries: local file -> download once & cache -> None (app falls back to a bubble map)."""
    global _geo
    if _geo: return _geo
    try:
        if not os.path.exists(GEO_FILE):
            r = requests.get(GEO_URL, timeout=8); r.raise_for_status()
            json.loads(r.content); open(GEO_FILE, "wb").write(r.content)
        _geo = json.load(open(GEO_FILE))
    except Exception as e:
        app.logger.warning("GeoJSON unavailable, using bubble map: %s", e)
    return _geo

def fj(fig, h=360):
    fig.update_layout(height=h, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter, Segoe UI, system-ui, sans-serif", color="#27403f"),
                      legend=dict(orientation="h", y=-0.15), title_font_size=15)
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

def row(name):
    if name not in DISTRICTS: name = DISTRICTS[0]
    return name, df[df.District == name].iloc[0]

@app.context_processor
def inject():
    return {"site": config.SITE, "districts_all": DISTRICTS, "CH": CH, "now": datetime.now()}

@app.template_filter("num")
def num(v, d=0): return f"{v:,.{d}f}"

# ---------- pages ----------
@app.route("/")
def index():
    stats = dict(avg_pov=df.Poverty_Rate_Pct.mean(), n=len(df), **{k: df[k].sum() for k in COLS})
    top = df.nlargest(10, "Priority").sort_values("Priority")
    f1 = go.Figure(go.Bar(x=top.Priority, y=top.District, orientation="h", marker_color=RED,
                          hovertemplate="%{y}: %{x}/100<extra></extra>"))
    f1.update_layout(title="Top 10 districts by Exclusion Priority Index", xaxis_range=[0, 100])
    s = df.sort_values("Poverty_Rate_Pct", ascending=False)
    f2 = go.Figure(go.Bar(x=s.District, y=s.Poverty_Rate_Pct, marker_color=np.where(s.Poverty_Rate_Pct > stats["avg_pov"], RED, TEAL)))
    f2.add_hline(y=stats["avg_pov"], line_dash="dot", annotation_text="District average")
    f2.update_layout(title="Poverty rate by district (%)", xaxis_tickangle=-60)
    f3 = go.Figure(go.Pie(labels=list(CH.values()), values=[stats[k] for k in COLS], hole=.6,
                          marker_colors=[TEAL, AMBER, "#5aa9e6"]))
    f3.update_layout(title="National channel mix")
    corr = float(np.corrcoef(df.Total_Reach, df.Poverty_Rate_Pct)[0, 1])
    hi, lo = df.loc[df.Poverty_Rate_Pct.idxmax()], df.loc[df.Poverty_Rate_Pct.idxmin()]
    zero = int((df.Digital_App_Pct == 0).sum())
    return render_template("index.html", stats=stats, corr=corr, hi=hi, lo=lo, zero=zero,
                           charts={"c1": fj(f1, 380), "c2": fj(f2, 380), "c3": fj(f3, 380)})

@app.route("/map")
def map_view():
    ind = request.args.get("indicator", "Digital_App_Pct")
    if ind not in CH and ind != "Poverty_Rate_Pct": ind = "Digital_App_Pct"
    label = CH.get(ind, "Poverty rate (%)")
    geo = get_geo()
    if geo:
        fm = px.choropleth_map(df, geojson=geo, locations="District", featureidkey="properties.shapeName", color=ind,
                               color_continuous_scale="Tealgrn", map_style="carto-positron", zoom=7, opacity=.75,
                               center={"lat": -1.94, "lon": 29.87}, labels={ind: label})
    else:  # offline fallback: bubbles at district centres
        d = df.assign(lat=df.District.map(lambda x: CENTROIDS[x][0]), lon=df.District.map(lambda x: CENTROIDS[x][1]))
        fm = px.scatter_map(d, lat="lat", lon="lon", size=d[ind].clip(lower=0) + 1, color=ind, hover_name="District",
                            color_continuous_scale="Tealgrn", size_max=32, zoom=7, map_style="carto-positron",
                            center={"lat": -1.94, "lon": 29.87}, labels={ind: label})
    fm.update_layout(coloraxis_colorbar_title="")
    fs = px.scatter(df, x=ind, y="Poverty_Rate_Pct", text="District", labels={ind: label, "Poverty_Rate_Pct": "Poverty rate (%)"})
    m, b = np.polyfit(df[ind], df.Poverty_Rate_Pct, 1)  # simple OLS trendline (no statsmodels needed)
    xs = np.array([df[ind].min(), df[ind].max()])
    fs.add_trace(go.Scatter(x=xs, y=m * xs + b, mode="lines", line=dict(color=AMBER, dash="dash"), name="Trend"))
    fs.update_traces(selector=dict(mode="markers+text"), textposition="top center", marker=dict(size=9, color=TEAL), textfont_size=9)
    fs.update_layout(showlegend=False, title=f"{label} vs poverty rate")
    r = float(np.corrcoef(df[ind], df.Poverty_Rate_Pct)[0, 1])
    return render_template("map.html", indicator=ind, r=r, fallback=not geo,
                           charts={"map": fj(fm, 520), "scatter": fj(fs, 520)})

@app.route("/profile")
def profile():
    name, d = row(request.args.get("district"))
    nat = df[COLS].mean()
    fb = go.Figure([go.Bar(name=name, x=list(CH.values()), y=[d[c] for c in COLS], marker_color=TEAL),
                    go.Bar(name="National average", x=list(CH.values()), y=[nat[c] for c in COLS], marker_color=GREY)])
    fb.update_layout(barmode="group", title=f"{name} vs national average")
    # percentile of each metric across districts
    pct = {CH[c]: round((df[c] <= d[c]).mean() * 100) for c in COLS}
    return render_template("profile.html", selected=name, d=d, avg=df.Poverty_Rate_Pct.mean(), pct=pct,
                           charts={"bar": fj(fb, 360)})

@app.route("/compare")
def compare():
    a, da = row(request.args.get("a", DISTRICTS[0]))
    b, db_ = row(request.args.get("b", DISTRICTS[1]))
    fc = go.Figure([go.Bar(name=n, x=list(CH.values()), y=[r[c] for c in COLS], marker_color=col)
                    for n, r, col in ((a, da, TEAL), (b, db_, AMBER))])
    fc.update_layout(barmode="group", title="Financial service reach")
    return render_template("compare.html", a=a, b=b, da=da, db=db_, charts={"cmp": fj(fc, 340)})

def sim_params():
    return {"gs": 1.5, "gb": 2.0}

@app.route("/simulator")
def simulator():
    name, d = row(request.args.get("district"))
    return render_template("simulator.html", selected=name, current=float(d.Poverty_Rate_Pct), k=sim_params())

@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    result, form = None, request.form
    if request.method == "POST":
        district = form.get("district")
        base = float(df.loc[df.District == district, "Poverty_Rate_Pct"].iloc[0]) if district in DISTRICTS else 40.0
        s = base - 15 * (form.get("has_bank") == "yes") - 5 * (form.get("has_momo") == "yes") - 10 * (form.get("has_savings_group") == "yes")
        s += {"agriculture": 12, "formal_salary": -15, "informal_trade": 5}.get(form.get("income_source"), 0)
        s = round(max(5.0, min(95.0, s)), 1)
        cat, col = (("High risk / vulnerable", RED) if s >= 45 else ("Medium risk", "#d98e04") if s >= 25 else ("Low risk / resilient", GREEN))
        result = dict(score=s, category=cat, color=col, district=district)
    return render_template("calculator.html", result=result, form=form)

@app.route("/action-plan")
def action_plan():
    name, d = row(request.args.get("district"))
    nat, recs = df.mean(numeric_only=True), []
    add = lambda i, t, x, lvl: recs.append(dict(icon=i, title=t, desc=x, level=lvl))
    if d.Bank_Loan_Pct < nat.Bank_Loan_Pct:
        add("🏦", "Expand formal credit access", "Bank loan reach is below the national average. Partner with Umurenge SACCOs to ease collateral requirements and launch micro-credit campaigns.", "critical")
    if d.Saving_Group_Pct > nat.Saving_Group_Pct:
        add("🤝", "Leverage saving groups (Ibimina)", "Participation in informal saving groups is high. Create pathways to register groups as cooperatives and link them to formal finance.", "opportunity")
    if d.Digital_App_Pct < nat.Digital_App_Pct:
        add("📱", "Boost digital financial literacy", "Digital finance usage is lagging. Deploy youth ambassadors to teach USSD mobile money and digital micro-savings.", "warning")
    else:
        add("🚀", "Deploy mobile-first aid", "Digital adoption is strong. Shift VUP cash transfers to mobile money for faster, more transparent delivery.", "opportunity")
    if d.Poverty_Rate_Pct > nat.Poverty_Rate_Pct:
        add("⚠️", "Urgent targeted social protection", "Poverty exceeds the national average. Prioritise this district for VUP public works and subsidised agricultural inputs.", "critical")
    if d.Digital_App_Pct == 0:
        add("🔎", "Verify digital finance data", "No digital-finance users are recorded here. Confirm whether this is a true gap or missing data before planning.", "warning")
    return render_template("action_plan.html", selected=name, d=d, recs=recs, nat=nat)

@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        dist, issue = request.form.get("district"), request.form.get("issue_type", "")
        desc = request.form.get("description", "").strip()[:1000]
        if request.form.get("website"): abort(400)  # honeypot: bots fill this hidden field
        if dist not in DISTRICTS or not issue:
            flash("Please choose a district and an issue type.", "error")
        else:
            with db() as c:
                c.execute("INSERT INTO reports (district, issue_type, description) VALUES (?,?,?)", (dist, issue, desc))
            flash("Thank you — your report was recorded.", "ok")
        return redirect(url_for("report"))
    with db() as c:
        recent = c.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 10").fetchall()
        by_issue = c.execute("SELECT issue_type, COUNT(*) n FROM reports GROUP BY issue_type ORDER BY n").fetchall()
        total = c.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    charts = {}
    if by_issue:
        f = go.Figure(go.Bar(x=[r["n"] for r in by_issue], y=[r["issue_type"] for r in by_issue], orientation="h", marker_color=TEAL))
        f.update_layout(title="Reports by issue type"); charts["issues"] = fj(f, 260)
    return render_template("report.html", reports=recent, total=total, charts=charts)

@app.route("/resources")
def resources():
    return render_template("resources.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        f = {k: request.form.get(k, "").strip() for k in ("name", "email", "subject", "message")}
        if request.form.get("website"): abort(400)
        if not f["name"] or not re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+$", f["email"]) or len(f["message"]) < 5:
            flash("Please enter your name, a valid email and a message.", "error")
        else:
            with db() as c:
                c.execute("INSERT INTO messages (name,email,subject,message) VALUES (?,?,?,?)",
                          (f["name"][:100], f["email"][:150], f["subject"][:150], f["message"][:2000]))
            flash("Message received — we will get back to you soon.", "ok")
        return redirect(url_for("contact"))
    return render_template("contact.html")

# ---------- API / ops ----------
@app.route("/api/districts")
def api_districts():
    return jsonify(df.round(2).to_dict(orient="records"))

@app.route("/download/data.csv")
def download():
    return Response(df.to_csv(index=False), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=rwanda_finance_poverty.csv"})

@app.route("/health")
def health():
    return jsonify(status="ok", districts=len(df))

@app.errorhandler(404)
def nf(e): return render_template("error.html", code=404, msg="We couldn't find that page."), 404
@app.errorhandler(400)
@app.errorhandler(500)
def err(e): return render_template("error.html", code=getattr(e, "code", 500), msg="Something went wrong. Please try again."), getattr(e, "code", 500)

@app.after_request
def headers(r):
    r.headers.setdefault("X-Content-Type-Options", "nosniff")
    r.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    return r

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1", port=int(os.getenv("PORT", 5000)))
