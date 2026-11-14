#!/usr/bin/env python3
"""
LIVE SOLAR CARD · today's PV forecast over Dhaka.

Pulls hourly shortwave irradiance and air temperature from Open-Meteo (free, no API key),
runs them through a simple PV model for a 5 kWp rooftop array, and writes:
  assets/solar-today.svg   the card shown on the profile
  data/solar.json          hourly output fractions, read by grid_engine.py for the G2 solar farm

PV model (per hour):
  T_cell = T_air + G * (NOCT - 20) / 800
  P      = P_stc * (G / 1000) * (1 + gamma * (T_cell - 25)) * eta_sys
"""
import json, math, os, re, sys, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG = os.path.join(ROOT, "assets", "solar-today-{theme}.svg")
DATA = os.path.join(ROOT, "data", "solar.json")
README = os.path.join(ROOT, "README.md")
TZ = ZoneInfo("Asia/Dhaka")
LAT, LON, PLACE = 23.8103, 90.4125, "DHAKA"

P_STC, GAMMA, NOCT, ETA_SYS = 5.0, -0.0040, 45.0, 0.86   # kWp, 1/°C, °C, system efficiency
GRID_EF = 0.67            # kg CO2 per kWh (assumed grid emission factor, edit if you have a better figure)

URL = (f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
       "&hourly=shortwave_radiation,temperature_2m,cloud_cover&daily=sunrise,sunset"
       "&timezone=Asia%2FDhaka&forecast_days=1")


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "profile-solar-card"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def model(ghi, tair):
    out = []
    for g, t in zip(ghi, tair):
        g = max(0.0, g or 0.0); t = t if t is not None else 25.0
        tc = t + g * (NOCT - 20) / 800
        out.append(max(0.0, P_STC * g / 1000 * (1 + GAMMA * (tc - 25)) * ETA_SYS))
    return out


MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"
BG, PANEL, EDGE, GRID = "#070b16", "#0b1222", "#1d2a47", "#122039"
YEL, AMB, GRN, TXT, DIM, BLU, RED = "#ffd23f", "#ffb000", "#39ff88", "#e6f1ff", "#6f83a8", "#3fa9ff", "#ff4d5e"
THEMES = {
    "dark": dict(BG="#070b16", PANEL="#0b1222", EDGE="#1d2a47", GRID="#122039", YEL="#ffd23f", AMB="#ffb000",
                 GRN="#39ff88", TXT="#e6f1ff", DIM="#6f83a8", BLU="#3fa9ff", RED="#ff4d5e"),
    "light": dict(BG="#ffffff", PANEL="#f6f8fa", EDGE="#d0d7de", GRID="#eef1f4", YEL="#bf8700", AMB="#bc4c00",
                  GRN="#1a7f37", TXT="#1f2328", DIM="#57606a", BLU="#0969da", RED="#cf222e"),
}


def _render(d, now, path):
    w, h = 1000, 330
    kw, ghi, temp, cloud = d["kw"], d["ghi"], d["temp"], d["cloud"]
    X0, X1, Y0, Y1 = 60, 650, 270, 80
    pmax = max(5.0, max(kw) * 1.1)
    X = lambda hr: X0 + hr * (X1 - X0) / 23
    Y = lambda p: Y0 - p / pmax * (Y0 - Y1)
    pts = [(X(i), Y(p)) for i, p in enumerate(kw)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = line + f" L{X(23):.1f},{Y0} L{X0},{Y0} Z"
    L = sum(math.dist(pts[i], pts[i + 1]) for i in range(23))
    energy = sum(kw)
    peak_i = max(range(24), key=lambda i: kw[i])
    g = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{MONO}">',
         f'<defs><linearGradient id="sun" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{YEL}" stop-opacity=".55"/>'
         f'<stop offset="1" stop-color="{YEL}" stop-opacity="0"/></linearGradient>'
         '<filter id="gl" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{BG}" stroke="{EDGE}" stroke-width="2"/>',
         f'<circle cx="26" cy="26" r="5" fill="{RED}"/><circle cx="44" cy="26" r="5" fill="{YEL}"/><circle cx="62" cy="26" r="5" fill="{BLU}"/>',
         f'<text x="84" y="31" font-size="12.5" fill="{DIM}" letter-spacing="1.5">LIVE SOLAR · {PLACE} {LAT:.2f}°N {LON:.2f}°E · '
         f'5 kWp ROOFTOP FORECAST · {d["date"]}</text>',
         f'<line x1="16" y1="46" x2="{w-16}" y2="46" stroke="{EDGE}"/>']
    for k in range(0, 6):
        p = pmax * k / 5; y = Y(p)
        g.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{GRID}"/>'
                 f'<text x="{X0-8}" y="{y+4:.1f}" text-anchor="end" font-size="10" fill="{DIM}">{p:.1f}</text>')
    for hr in range(0, 24, 3):
        g.append(f'<text x="{X(hr):.1f}" y="{Y0+18}" text-anchor="middle" font-size="10" fill="{DIM}">{hr:02d}h</text>')
    g.append(f'<text x="{X0-8}" y="66" text-anchor="end" font-size="10" fill="{DIM}">kW</text>')
    # cloud cover bars at the bottom
    for i, c in enumerate(cloud):
        if c:
            g.append(f'<rect x="{X(i)-9:.1f}" y="{Y0-c*0.25:.1f}" width="18" height="{c*0.25:.1f}" fill="{BLU}" opacity=".18"/>')
    g.append(f'<path d="{area}" fill="url(#sun)" opacity=".35"/><path d="{line}" fill="none" stroke="{YEL}" stroke-width="2" opacity=".45"/>')
    g.append(f'<path d="{area}" fill="url(#sun)" opacity="0"><animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.35;.5;.92;1" dur="8s" repeatCount="indefinite"/></path>')
    g.append(f'<path d="{line}" fill="none" stroke="{YEL}" stroke-width="3" filter="url(#gl)" stroke-dasharray="{L:.0f}" stroke-dashoffset="{L:.0f}">'
             f'<animate attributeName="stroke-dashoffset" values="{L:.0f};0;0;{L:.0f}" keyTimes="0;.45;.92;1" dur="8s" repeatCount="indefinite"/></path>')
    # NOW marker
    hn = now.hour + now.minute / 60
    if d["date"] == now.strftime("%Y-%m-%d"):
        xn = X0 + hn * (X1 - X0) / 23
        pn = kw[min(23, now.hour)]
        g.append(f'<line x1="{xn:.1f}" y1="{Y1-10}" x2="{xn:.1f}" y2="{Y0}" stroke="{RED}" stroke-dasharray="4 3"/>'
                 f'<circle cx="{xn:.1f}" cy="{Y(pn):.1f}" r="5" fill="{RED}"><animate attributeName="r" values="4;8;4" dur="1.4s" repeatCount="indefinite"/></circle>'
                 f'<text x="{xn:.1f}" y="{Y1-14}" text-anchor="middle" font-size="10" font-weight="700" fill="{RED}">NOW {pn:.2f} kW</text>')
    # stats panel
    stats = [("ENERGY TODAY", f"{energy:.1f} kWh", YEL),
             ("PEAK OUTPUT", f"{kw[peak_i]:.2f} kW @ {peak_i:02d}:00", YEL),
             ("PEAK IRRADIANCE", f"{max(ghi):.0f} W/m²", AMB),
             ("AIR TEMP", f"{min(temp):.0f}–{max(temp):.0f} °C", TXT),
             ("DAYLIGHT", f"{d['sunrise']} → {d['sunset']}", TXT),
             ("CO₂ AVOIDED", f"≈ {energy*GRID_EF:.1f} kg", GRN)]
    for i, (k, v, c) in enumerate(stats):
        col, row = i % 2, i // 2
        x, y = 690 + col * 150, 82 + row * 66
        g.append(f'<text x="{x}" y="{y}" font-size="9.5" fill="{DIM}" letter-spacing="1.2">{k}</text>'
                 f'<text x="{x}" y="{y+22}" font-size="{15 if len(v) < 14 else 12.5}" font-weight="700" fill="{c}">{v}</text>')
    src = "Open-Meteo forecast" if d.get("live") else "clear-sky estimate (forecast unavailable)"
    g.append(f'<text x="690" y="300" font-size="9.5" fill="{DIM}">source: {src}</text>'
             f'<text x="690" y="314" font-size="9.5" fill="{DIM}">model: NOCT {NOCT:.0f}°C · γ {GAMMA*100:.1f}%/°C · η {ETA_SYS:.2f}</text>')
    g.append(f'<text x="{X0}" y="314" font-size="9.5" fill="{DIM}">blue bars = cloud cover · this curve also drives the G2 solar farm in the live grid</text>')
    g.append('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(g) + "\n")


def render(d, now):
    for theme, pal in THEMES.items():
        globals().update(pal)
        _render(d, now, SVG.format(theme=theme))


def clear_sky(now):
    ghi, temp = [], []
    for hr in range(24):
        s = math.sin(math.pi * (hr + 0.5 - 6) / 12)
        ghi.append(max(0.0, 900 * s ** 1.3) if s > 0 else 0.0)
        temp.append(24 + 6 * max(0.0, math.sin(math.pi * (hr - 8) / 14)))
    return dict(date=now.strftime("%Y-%m-%d"), ghi=ghi, temp=temp, cloud=[0] * 24,
                sunrise="06:00", sunset="18:00", live=False)


def main():
    now = datetime.now(TZ)
    offline = "--offline" in sys.argv
    try:
        if offline:
            raise RuntimeError("offline mode")
        raw = fetch()
        hr = raw["hourly"]
        d = dict(date=hr["time"][0][:10], ghi=hr["shortwave_radiation"][:24], temp=hr["temperature_2m"][:24],
                 cloud=hr.get("cloud_cover", [0] * 24)[:24], sunrise=raw["daily"]["sunrise"][0][-5:],
                 sunset=raw["daily"]["sunset"][0][-5:], live=True)
    except Exception as e:
        print("forecast unavailable:", e)
        if os.path.exists(DATA) and not offline:
            with open(DATA) as f:
                old = json.load(f)
            if old.get("date") == now.strftime("%Y-%m-%d"):
                print("keeping today's earlier forecast"); return
        d = clear_sky(now)
    d["ghi"] = [g or 0.0 for g in d["ghi"]]
    d["temp"] = [t if t is not None else 25.0 for t in d["temp"]]
    d["cloud"] = [c or 0 for c in d["cloud"]]
    d["kw"] = model(d["ghi"], d["temp"])
    d["hourly_fraction"] = [p / P_STC for p in d["kw"]]
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    with open(DATA, "w") as f:
        json.dump(d, f, indent=1)
    render(d, now)
    # cache-bust the image in the README
    with open(README, encoding="utf-8") as f:
        s = f.read()
    s = re.sub(r'assets/solar-today-(light|dark)\.svg(\?v=[0-9T-]+)?', lambda mm: f'assets/solar-today-{mm.group(1)}.svg?v={now.strftime("%Y%m%dT%H")}', s)
    with open(README, "w", encoding="utf-8") as f:
        f.write(s)
    print(f"solar card: {sum(d['kw']):.1f} kWh, live={d['live']}")


if __name__ == "__main__":
    main()
