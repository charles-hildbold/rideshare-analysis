"""Builds index.html from data/summary.json.

Every number on the page comes from the summary file, which was produced from
the raw Uber, Lyft and Gridwise exports (kept out of this repo).
Run: python3 build.py
"""
import json
from datetime import date
from html import escape

D = json.load(open("data/summary.json"))
L = D["lifetime"]

BAR = "#3D5A99"
HIGHLIGHT = "#A8262F"
INK = "#1E2638"
INK2 = "#4A5266"
GRID = "#D5D8D2"


def money(v, cents=False):
    return f"${v:,.2f}" if cents else f"${round(v):,}"


def bar_path(x, y, w, h, r=4):
    """A bar with rounded top corners, square at the baseline."""
    r = min(r, w / 2, h)
    if h <= 0:
        return ""
    return (f"M{x:.1f},{y + h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
            f"H{x + w - r:.1f} Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y + h:.1f} Z")


def bar_chart(items, ymax, ystep, yfmt, width=760, height=300, label_every=1,
              direct=None, aria=""):
    """items: list of dict(label, value, tip, highlight). Single series."""
    left, right, top, bottom = 56, 8, 16, 34
    pw, ph = width - left - right, height - top - bottom
    n = len(items)
    slot = pw / n
    bw = max(slot - 2, 1)  # 2px surface gap between bars
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(aria)}" class="chart">']
    v = 0
    while v <= ymax + 1e-9:
        y = top + ph - (v / ymax) * ph
        out.append(f'<line x1="{left}" x2="{width - right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" class="ax">{yfmt(v)}</text>')
        v += ystep
    for i, it in enumerate(items):
        x = left + i * slot + 1
        h = (it["value"] / ymax) * ph
        y = top + ph - h
        color = HIGHLIGHT if it.get("highlight") else BAR
        out.append(f'<g class="hit" data-tip="{escape(it["tip"])}">'
                   f'<rect x="{left + i * slot:.1f}" y="{top}" width="{slot:.1f}" height="{ph}" fill="transparent"/>'
                   f'<path d="{bar_path(x, y, bw, h)}" fill="{color}"/></g>')
        if i % label_every == 0 or it.get("force_label"):
            out.append(f'<text x="{x + bw / 2:.1f}" y="{height - 12}" text-anchor="middle" class="ax">{escape(it["label"])}</text>')
        if direct and it.get("direct"):
            out.append(f'<text x="{x + bw / 2:.1f}" y="{y - 7:.1f}" text-anchor="middle" class="dl">{escape(it["direct"])}</text>')
    out.append(f'<line x1="{left}" x2="{width - right}" y1="{top + ph}" y2="{top + ph}" stroke="{INK2}" stroke-width="1"/>')
    out.append("</svg>")
    return "".join(out)


# Monthly chart
months = []
for m in D["monthly"]:
    y, mo, _ = map(int, m["date"].split("-"))
    d = date(y, mo, 1)
    name = d.strftime("%b %Y")
    partial = (y == 2026 and mo == 5)
    settle = (y == 2024 and mo == 2)
    tip = f"{name}{' (May 1 to 9 only)' if partial else ''}: {money(m['earn'])} net, {m['hours']:,.0f} hours, ${m['dollar_per_hour']:.2f}/hr"
    if settle:
        tip += ". Includes the $1,868 EV settlement."
    months.append(dict(label=str(y) if mo == 1 else "", value=m["earn"], tip=tip,
                       highlight=settle, force_label=(mo == 1),
                       direct="EV settlement" if settle else None))
monthly_svg = bar_chart(months, 12000, 4000, lambda v: f"${int(v/1000)}k" if v else "$0", label_every=999,
                        direct=True, aria="Monthly net earnings, January 2023 to May 2026")

# Day of week, dollars per clocked hour
dow_full = {"Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", "Thu": "Thursday",
            "Fri": "Friday", "Sat": "Saturday", "Sun": "Sunday"}
dows = []
for d in D["dow"]:
    dows.append(dict(label=d["day"], value=d["dollar_per_hour"],
                     tip=f"{dow_full[d['day']]}: ${d['dollar_per_hour']:.2f}/hr, {money(d['dollar_per_day'])} per day, {d['days']} days driven",
                     highlight=(d["day"] == "Sat"),
                     direct=f"${d['dollar_per_hour']:.2f}" if d["day"] in ("Sat", "Mon") else None))
dow_svg = bar_chart(dows, 60, 20, lambda v: f"${int(v)}", width=760, height=280, direct=True,
                    aria="Net earnings per clocked hour by day of week")

# Surge tiers, average fare
surge = []
for s in D["surge"]:
    surge.append(dict(label=s["tier"], value=s["avg_fare"],
                      tip=f"{s['tier']}: {s['trips']:,} trips, ${s['avg_fare']:.2f} average fare",
                      direct=f"${s['avg_fare']:.2f}"))
surge_svg = bar_chart(surge, 40, 10, lambda v: f"${int(v)}", width=760, height=260, direct=True,
                      aria="Average Uber fare by surge tier")

# Take rate line
def take_rate_svg():
    tr = D["take_rate"]
    width, height, left, right, top, bottom = 760, 250, 56, 40, 34, 34
    pw, ph = width - left - right, height - top - bottom
    ymax = 50
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Uber take rate by year" class="chart">']
    for v in range(0, 51, 10):
        y = top + ph - v / ymax * ph
        out.append(f'<line x1="{left}" x2="{width - right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}"/>')
        out.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" class="ax">{v}%</text>')
    pts = []
    for i, t in enumerate(tr):
        inset = 40
        x = left + inset + i * ((pw - 2 * inset) / (len(tr) - 1))
        y = top + ph - t["rate"] / ymax * ph
        pts.append((x, y, t))
    out.append('<polyline fill="none" stroke="%s" stroke-width="2" points="%s"/>' % (BAR, " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in pts)))
    for x, y, t in pts:
        lab = f"{t['year']}" + (" so far" if t["year"] == 2026 else "")
        out.append(f'<g class="hit" data-tip="{lab}: Uber kept {t["rate"]:g}% of what riders paid">'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="transparent"/>'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{BAR}" stroke="#F2F3F1" stroke-width="2"/></g>')
        out.append(f'<text x="{x:.1f}" y="{y - 12:.1f}" text-anchor="middle" class="dl">{t["rate"]:g}%</text>')
        out.append(f'<text x="{x:.1f}" y="{height - 12}" text-anchor="middle" class="ax">{lab}</text>')
    out.append(f'<line x1="{left}" x2="{width - right}" y1="{top + ph}" y2="{top + ph}" stroke="{INK2}"/>')
    out.append("</svg>")
    return "".join(out)


# Heatmap: rows Monday..Sunday, columns hour 0..23
def heatmap_html():
    cells = {(c["dow"], c["hour"]): c["count"] for c in D["heatmap"]}
    mx = max(cells.values())
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    out = ['<div class="heat" role="img" aria-label="Completed Uber trips by hour and day of week">']
    out.append('<span></span>' + "".join(
        f'<span class="hh">{("12a" if h == 0 else "12p" if h == 12 else (str(h) + "a" if h < 12 else str(h - 12) + "p")) if h % 3 == 0 else ""}</span>'
        for h in range(24)))
    for d in range(7):
        out.append(f'<span class="hd">{names[d]}</span>')
        for h in range(24):
            n = cells.get((d, h), 0)
            a = 0 if n == 0 else 0.08 + 0.92 * (n / mx)
            hr = f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"
            out.append(f'<span class="hc hit" style="background:rgba(61,90,153,{a:.3f})" data-tip="{dow_full[names[d]]}, {hr}: {n:,} trips"></span>')
    out.append("</div>")
    return "".join(out)


# Numbers used in the copy
sat = next(d for d in D["dow"] if d["day"] == "Sat")
mon = next(d for d in D["dow"] if d["day"] == "Mon")
tue = next(d for d in D["dow"] if d["day"] == "Tue")
sat_vs_mon = round((sat["dollar_per_hour"] / mon["dollar_per_hour"] - 1) * 100)
surge_total = sum(s["trips"] for s in D["surge"])
no_surge_pct = round(D["surge"][0]["trips"] / surge_total * 100)
top_surge = D["surge"][-1]
surge_mult = top_surge["avg_fare"] / D["surge"][0]["avg_fare"]
hourly_total = sum(h["trips"] for h in D["hourly"])
evening_pct = round(sum(h["trips"] for h in D["hourly"] if 15 <= h["hour"] <= 23) / hourly_total * 100)
ap = D["airport"]
ap_premium = ap["airport_avg_fare"] / ap["city_avg_fare"]
ap_share = ap["airport_trips"] / (ap["airport_trips"] + ap["city_trips"]) * 100
years = (D["lifetime"]["days_period"]) / 365.25
ap_per_year = ap["airport_trips"] / years
ap_extra = ap_per_year * (ap["airport_avg_fare"] - ap["city_avg_fare"])
ss = D["service_split"]
uber_share = ss["uber_trips"] / (ss["uber_trips"] + ss["lyft_trips"]) * 100
app_rate = 95.00
overstate = app_rate / L["dollar_per_hour"]
monthly_vals = [m["earn"] for m in D["monthly"] if not m["date"].startswith(("2024-02", "2026-05"))]

annual_rows = "".join(
    f'<tr><th scope="row">{a["year"]}{" so far" if a["year"] == 2026 else ""}</th>'
    f'<td>{a["days"]}</td><td>{a["trips"]:,}</td><td>{money(a["earn"])}</td>'
    f'<td>{a["hours"]:,.1f}</td><td>{round(a["miles"]):,}</td>'
    f'<td><b>${a["dollar_per_hour"]:.2f}</b></td><td>{money(a["ded"])}</td></tr>'
    for a in D["annual"])
annual_total = (f'<tr class="tot"><th scope="row">Total</th><td>{L["days_active"]:,}</td><td>{L["trips"]:,}</td>'
                f'<td>{money(L["earn"])}</td><td>{L["hours"]:,.1f}</td><td>{round(L["miles"]):,}</td>'
                f'<td><b>${L["dollar_per_hour"]:.2f}</b></td><td>{money(L["tax_ded"])}</td></tr>')

page = open("template.html").read()
fills = {
    "MONTHLY_SVG": monthly_svg,
    "DOW_SVG": dow_svg,
    "SURGE_SVG": surge_svg,
    "TAKE_SVG": take_rate_svg(),
    "HEATMAP": heatmap_html(),
    "ANNUAL_ROWS": annual_rows + annual_total,
    "EARN": money(L["earn"]),
    "TRIPS": f'{L["trips"]:,}',
    "HOURS": f'{round(L["hours"]):,}',
    "MILES": f'{round(L["miles"]):,}',
    "RATE": f'${L["dollar_per_hour"]:.2f}',
    "PER_MILE": f'${L["dollar_per_mile"]:.2f}',
    "PER_TRIP": f'${L["dollar_per_trip"]:.2f}',
    "RIDES_HR": f'{L["rides_per_hour"]:.2f}',
    "SPEED": f'{L["avg_speed_mph"]:.1f}',
    "DAYS": f'{L["days_active"]:,}',
    "OVERSTATE": f"{overstate:.1f}",
    "SAT_HR": f'${sat["dollar_per_hour"]:.2f}',
    "MON_HR": f'${mon["dollar_per_hour"]:.2f}',
    "SAT_DAY": money(sat["dollar_per_day"]),
    "TUE_DAY": money(tue["dollar_per_day"]),
    "SAT_VS_MON": str(sat_vs_mon),
    "EVENING_PCT": str(evening_pct),
    "NO_SURGE_PCT": str(no_surge_pct),
    "TOP_SURGE_TRIPS": f'{top_surge["trips"]:,}',
    "TOP_SURGE_FARE": f'${top_surge["avg_fare"]:.2f}',
    "NO_SURGE_FARE": f'${D["surge"][0]["avg_fare"]:.2f}',
    "SURGE_MULT": f"{surge_mult:.1f}",
    "AP_FARE": f'${ap["airport_avg_fare"]:.2f}',
    "CITY_FARE": f'${ap["city_avg_fare"]:.2f}',
    "AP_PREMIUM": f"{ap_premium:.1f}",
    "AP_TRIPS": f'{ap["airport_trips"]:,}',
    "AP_SHARE": f"{ap_share:.1f}",
    "AP_EXTRA": f"${round(ap_extra, -2):,.0f}",
    "TIPS": money(D["tips_total"]),
    "TIP_RATE": f'{D["tip_rate"]:.1f}',
    "UBER_SHARE": f"{round(uber_share)}",
    "UBER_TRIP": f'${ss["uber_per_trip"]:.2f}',
    "LYFT_TRIP": f'${ss["lyft_per_trip"]:.2f}',
    "LYFT_TRIPS": f'{ss["lyft_trips"]:,}',
    "SETTLE": f'${D["lifetime"]["settlement"]:,.2f}',
    "TOP_DAY": f'${D["top_day"]["earn"]:,.2f}',
    "MONTH_LOW": f"${round(min(monthly_vals), -2):,.0f}",
    "MONTH_HIGH": f"${round(max(monthly_vals), -2):,.0f}",
    "TR_FIRST": f'{D["take_rate"][0]["rate"]:g}%',
    "TR_LAST": f'{D["take_rate"][-1]["rate"]:g}%',
}
for k, v in fills.items():
    page = page.replace("{{" + k + "}}", v)
assert "{{" not in page, page[page.index("{{"):page.index("{{") + 40]
open("index.html", "w").write(page)
print("built index.html")
