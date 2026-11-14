#!/usr/bin/env python3
"""
LIVE GRID ENGINE · multiplayer power-flow game for the AHShaikat profile.

A visitor opens an issue titled  grid|toggle|CB3  (or  grid|restore).
GitHub Actions runs this script, which:
  1. switches the breaker,
  2. solves a full AC power flow (Newton-Raphson, polar form) on a 6-bus grid,
  3. lets overcurrent relays trip overloaded lines (which may cascade),
  4. declares a voltage collapse / blackout if the solution diverges, then black-starts,
  5. re-draws assets/live-grid-{light,dark}.svg and the control table inside README.md,
  6. writes a reply for the bot to post on the issue.

The solar plant G2 follows today's real irradiance over Dhaka (data/solar.json,
written by tools/solar_card.py), so the grid behaves differently at noon and at night.

Usage:
  python tools/grid_engine.py --title "grid|toggle|CB3" --user someone --reply reply.md
  python tools/grid_engine.py --refresh            # re-solve with the latest solar output
"""
import argparse, json, math, os, re
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "grid_state.json")
SOLAR = os.path.join(ROOT, "data", "solar.json")
SVG = os.path.join(ROOT, "assets", "live-grid-{theme}.svg")
README = os.path.join(ROOT, "README.md")
REPO = os.environ.get("GITHUB_REPOSITORY", "AHShaikat/AHShaikat")
TZ = ZoneInfo("Asia/Dhaka")
BASE_MVA = 100.0

# ----------------------------------------------------------------------------- network data
# bus: name, type (slack/pv/pq), P load MW, Q load MVAr, V setpoint, x, y on the drawing
BUSES = {
    1: dict(name="BUS 1 · G1 THERMAL", kind="slack", pl=0,   ql=0,   vset=1.04, x=110, y=150),
    2: dict(name="BUS 2 · CITY",       kind="pq",    pl=38,  ql=14,  vset=1.0,  x=430, y=110),
    3: dict(name="BUS 3 · SUBURB",     kind="pq",    pl=42,  ql=18,  vset=1.0,  x=300, y=380),
    4: dict(name="BUS 4 · G2 SOLAR",   kind="pv",    pl=0,   ql=0,   vset=1.02, x=740, y=130),
    5: dict(name="BUS 5 · CAMPUS",     kind="pq",    pl=49,  ql=21,  vset=1.0,  x=600, y=400),
    6: dict(name="BUS 6 · INDUSTRY",   kind="pq",    pl=60,  ql=28,  vset=1.0,  x=880, y=370),
}
SOLAR_MW_MAX = 150.0                 # nameplate of the G2 solar farm
G2_QLIM = (-80.0, 120.0)              # MVAr capability of the solar inverters
# line breaker: from, to, r, x, b (pu on 100 MVA), thermal rating MVA
LINES = {
    "CB1": (1, 2, 0.020, 0.10, 0.04, 150),
    "CB2": (1, 3, 0.030, 0.12, 0.04, 150),
    "CB3": (2, 3, 0.040, 0.16, 0.03, 100),
    "CB4": (2, 4, 0.030, 0.14, 0.03, 120),
    "CB5": (3, 5, 0.035, 0.15, 0.03, 110),
    "CB6": (4, 5, 0.030, 0.13, 0.03, 120),
    "CB7": (4, 6, 0.025, 0.11, 0.03, 130),
    "CB8": (5, 6, 0.040, 0.17, 0.03, 100),
}
TRIP_AT = 1.25                       # relay trips a line above 125 % of its rating
COLLAPSE_V = 0.80                    # below this the case is treated as a voltage collapse


# ----------------------------------------------------------------------------- solar input
def solar_mw(now):
    """G2 output from today's irradiance curve (fraction of nameplate per hour)."""
    try:
        with open(SOLAR) as f:
            s = json.load(f)
        frac = s["hourly_fraction"][now.hour]
        return SOLAR_MW_MAX * max(0.0, min(1.0, frac)), s.get("date") == now.strftime("%Y-%m-%d")
    except Exception:
        # no data yet: a clear-sky bell between 06:00 and 18:00
        h = now.hour + now.minute / 60
        return SOLAR_MW_MAX * max(0.0, math.sin(math.pi * (h - 6) / 12)) * 0.8, False


# ----------------------------------------------------------------------------- power flow
def energized_buses(closed):
    """Buses connected to the slack through closed breakers (no islanded operation)."""
    seen, stack = {1}, [1]
    while stack:
        b = stack.pop()
        for cb, (f, t, *_) in LINES.items():
            if closed[cb] and b in (f, t):
                o = t if b == f else f
                if o not in seen:
                    seen.add(o); stack.append(o)
    return sorted(seen)


def newton_raphson(closed, p_solar, max_iter=25, tol=1e-8):
    live = energized_buses(closed)
    idx = {b: i for i, b in enumerate(live)}
    n = len(live)
    Y = np.zeros((n, n), dtype=complex)
    for cb, (f, t, r, x, b, _) in LINES.items():
        if closed[cb] and f in idx and t in idx:
            y = 1 / complex(r, x); i, j = idx[f], idx[t]
            Y[i, i] += y + 1j * b / 2; Y[j, j] += y + 1j * b / 2
            Y[i, j] -= y; Y[j, i] -= y
    kind = {b: BUSES[b]["kind"] for b in live}
    Pg = {b: 0.0 for b in live}
    if 4 in idx:
        Pg[4] = p_solar
    Psch = np.array([(Pg[b] - BUSES[b]["pl"]) / BASE_MVA for b in live])
    Qsch = np.array([-BUSES[b]["ql"] / BASE_MVA for b in live])
    Vm = np.array([BUSES[b]["vset"] if kind[b] != "pq" else 1.0 for b in live])
    Va = np.zeros(n)
    q_limited = False

    for outer in range(2):                       # second pass if G2 hits its Q limit
        pv = [idx[b] for b in live if kind[b] == "pv"]
        pq = [idx[b] for b in live if kind[b] == "pq"]
        pvpq = pv + pq
        converged, it = False, 0
        for it in range(1, max_iter + 1):
            V = Vm * np.exp(1j * Va)
            I = Y @ V
            S = V * np.conj(I)
            mis = np.r_[S.real[pvpq] - Psch[pvpq], S.imag[pq] - Qsch[pq]]
            err = np.max(np.abs(mis)) if mis.size else 0.0
            if err < tol:
                converged = True; break
            if not np.all(np.isfinite(mis)) or err > 1e3:
                break
            dS_dVa = 1j * np.diag(V) @ np.conj(np.diag(I) - Y @ np.diag(V))
            dS_dVm = np.diag(V) @ np.conj(Y @ np.diag(V / Vm)) + np.conj(np.diag(I)) @ np.diag(V / Vm)
            J = np.block([[dS_dVa.real[np.ix_(pvpq, pvpq)], dS_dVm.real[np.ix_(pvpq, pq)]],
                          [dS_dVa.imag[np.ix_(pq, pvpq)],   dS_dVm.imag[np.ix_(pq, pq)]]])
            try:
                dx = np.linalg.solve(J, -mis)
            except np.linalg.LinAlgError:
                break
            Va[pvpq] += dx[:len(pvpq)]
            Vm[pq] += dx[len(pvpq):]
            if np.any(Vm <= 0.05):
                break
        if not converged:
            return dict(converged=False, iterations=it, live=live)
        # generator reactive power check for G2
        V = Vm * np.exp(1j * Va); S = V * np.conj(Y @ V)
        if 4 in idx and kind[4] == "pv":
            qg = S.imag[idx[4]] * BASE_MVA + BUSES[4]["ql"]
            lo, hi = G2_QLIM
            if qg > hi or qg < lo:
                kind[4] = "pq"; q_limited = True
                Qsch[idx[4]] = (min(max(qg, lo), hi) - BUSES[4]["ql"]) / BASE_MVA
                continue
        break

    V = Vm * np.exp(1j * Va); S = V * np.conj(Y @ V)
    flows, losses = {}, 0.0
    for cb, (f, t, r, x, b, rating) in LINES.items():
        if closed[cb] and f in idx and t in idx:
            y = 1 / complex(r, x); vf, vt = V[idx[f]], V[idx[t]]
            sft = vf * np.conj((vf - vt) * y + vf * 1j * b / 2) * BASE_MVA
            stf = vt * np.conj((vt - vf) * y + vt * 1j * b / 2) * BASE_MVA
            losses += (sft + stf).real
            flows[cb] = dict(p=sft.real, q=sft.imag, mva=max(abs(sft), abs(stf)),
                             loading=max(abs(sft), abs(stf)) / rating)
    gen = {1: S[idx[1]] * BASE_MVA}
    if 4 in idx:
        gen[4] = complex(p_solar, S.imag[idx[4]] * BASE_MVA + BUSES[4]["ql"])
    return dict(converged=True, iterations=it, mismatch=float(err), live=live,
                vm={b: float(Vm[idx[b]]) for b in live},
                va={b: float(np.degrees(Va[idx[b]])) for b in live},
                flows=flows, losses=float(losses),
                gen={b: [float(v.real), float(v.imag)] for b, v in gen.items()},
                q_limited=q_limited)


def simulate(closed, p_solar):
    """Solve, then let the relays act until the grid settles or collapses."""
    events = []
    for _ in range(len(LINES) + 1):
        sol = newton_raphson(closed, p_solar)
        if not sol["converged"] or min(sol["vm"].values()) < COLLAPSE_V:
            events.append(("COLLAPSE", "Newton-Raphson diverged: voltage collapse, total blackout"
                           if not sol["converged"] else
                           f"voltage fell to {min(sol['vm'].values()):.2f} pu: under-voltage load shedding failed, blackout"))
            return None, events
        worst = max(sol["flows"].items(), key=lambda kv: kv[1]["loading"], default=None)
        if worst and worst[1]["loading"] > TRIP_AT:
            cb = worst[0]
            closed[cb] = False
            events.append(("TRIP", f"{cb} tripped by overcurrent relay at {worst[1]['loading']*100:.0f}% loading"))
            continue
        if not any(BUSES[b]["pl"] > 0 for b in sol["live"]):
            events.append(("COLLAPSE", "the cascade disconnected every load from the generator: total blackout"))
            return None, events
        return sol, events
    return sol, events


def alarms(sol):
    out = []
    if sol is None:
        return ["TOTAL BLACKOUT"]
    for b, v in sol["vm"].items():
        if v < 0.95: out.append(f"UNDER-VOLTAGE B{b} {v:.3f} pu")
        if v > 1.05: out.append(f"OVER-VOLTAGE B{b} {v:.3f} pu")
    for cb, fl in sol["flows"].items():
        if fl["loading"] > 1.0: out.append(f"OVERLOAD {cb} {fl['loading']*100:.0f}%")
    dead = [b for b in BUSES if b not in sol["live"]]
    if dead: out.append("DE-ENERGIZED " + ", ".join(f"B{b}" for b in dead))
    if sol.get("q_limited"): out.append("G2 AT Q-LIMIT")
    return out


# ----------------------------------------------------------------------------- state
def default_state():
    return dict(closed={cb: True for cb in LINES}, ops=0, collapses=0, trips=0,
                operators={}, log=[], solution=None, updated=None, solar_mw=0.0)


def load_state():
    try:
        with open(STATE) as f:
            s = json.load(f)
        for k, v in default_state().items():
            s.setdefault(k, v)
        return s
    except FileNotFoundError:
        return default_state()


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(s, f, indent=1)


# ----------------------------------------------------------------------------- drawing
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"
BG, PANEL, EDGE, GRID = "#070b16", "#0b1222", "#1d2a47", "#122039"
RED, YEL, BLU, GRN, AMB, TXT, DIM, DEAD = "#ff4d5e", "#ffd23f", "#3fa9ff", "#39ff88", "#ffb000", "#e6f1ff", "#6f83a8", "#2b3756"
THEMES = {
    "dark": dict(BG="#070b16", PANEL="#0b1222", EDGE="#1d2a47", GRID="#122039", RED="#ff4d5e", YEL="#ffd23f",
                 BLU="#3fa9ff", GRN="#39ff88", AMB="#ffb000", TXT="#e6f1ff", DIM="#6f83a8", DEAD="#2b3756"),
    "light": dict(BG="#ffffff", PANEL="#f6f8fa", EDGE="#d0d7de", GRID="#eef1f4", RED="#cf222e", YEL="#bf8700",
                  BLU="#0969da", GRN="#1a7f37", AMB="#bc4c00", TXT="#1f2328", DIM="#57606a", DEAD="#c8cfd6"),
}


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_svg(state, path):
    sol, closed = state["solution"], state["closed"]
    w, h = 1000, 600
    live = set(sol["live"]) if sol else set()
    g = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{MONO}">',
         '<defs><filter id="gl" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.5" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
         f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{BG}" stroke="{EDGE}" stroke-width="2"/>',
         f'<circle cx="26" cy="26" r="5" fill="{RED}"/><circle cx="44" cy="26" r="5" fill="{YEL}"/><circle cx="62" cy="26" r="5" fill="{BLU}"/>']
    if sol:
        head = (f"LIVE GRID · AC POWER FLOW · NEWTON-RAPHSON CONVERGED IN {sol['iterations']} ITER · "
                f"MISMATCH {sol['mismatch']:.0e} PU")
    else:
        head = "LIVE GRID · BLACKOUT · BLACK-START IN PROGRESS"
    g.append(f'<text x="84" y="31" font-size="12.5" fill="{DIM}" letter-spacing="1.5">{head}</text>')
    g.append(f'<line x1="16" y1="46" x2="{w-16}" y2="46" stroke="{EDGE}"/>')
    for x in range(40, w - 20, 40):
        g.append(f'<line x1="{x}" y1="52" x2="{x}" y2="478" stroke="{GRID}" stroke-opacity=".45"/>')

    # lines
    for cb, (f, t, *_rest) in LINES.items():
        bf, bt = BUSES[f], BUSES[t]
        x1, y1, x2, y2 = bf["x"], bf["y"], bt["x"], bt["y"]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        fl = sol["flows"].get(cb) if sol else None
        if closed[cb] and fl:
            ld = fl["loading"]
            col = GRN if ld < 0.7 else (AMB if ld <= 1.0 else RED)
            if fl["p"] < 0:                          # draw arrows in the direction of real power
                x1, y1, x2, y2 = x2, y2, x1, y1
            dur = max(0.35, 2.2 - 1.8 * min(ld, 1.0))
            g.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-opacity=".18" stroke-width="9"/>')
            g.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="3" stroke-dasharray="10 9">'
                     f'<animate attributeName="stroke-dashoffset" from="19" to="0" dur="{dur:.2f}s" repeatCount="indefinite"/></line>')
            g.append(f'<rect x="{mx-9}" y="{my-9}" width="18" height="18" fill="{RED}" stroke="#ffc2c8"/>')
            lab = f"{cb} · {abs(fl['p']):.0f} MW · {ld*100:.0f}%"
            tc = col
        else:
            g.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{DEAD}" stroke-width="2.5" stroke-dasharray="4 6"/>')
            g.append(f'<rect x="{mx-9}" y="{my-9}" width="18" height="18" fill="{BG}" stroke="{GRN}" stroke-width="2"/>')
            lab = f"{cb} · {'OPEN' if not closed[cb] else 'DEAD'}"
            tc = DIM
        tw = len(lab) * 7.0 + 12
        g.append(f'<rect x="{mx-tw/2}" y="{my+13}" width="{tw}" height="17" rx="4" fill="{BG}" fill-opacity=".85"/>'
                 f'<text x="{mx}" y="{my+25}" text-anchor="middle" font-size="11" fill="{tc}">{lab}</text>')

    # buses, generators, loads
    for b, d in BUSES.items():
        x, y = d["x"], d["y"]
        on = b in live
        col = TXT if on else DEAD
        barc = (YEL if b in (1, 4) else BLU) if on else DEAD
        g.append(f'<line x1="{x-52}" y1="{y}" x2="{x+52}" y2="{y}" stroke="{barc}" stroke-width="8" stroke-linecap="round"/>')
        g.append(f'<text x="{x}" y="{y-34 if b in (1, 2, 4) else y+58}" text-anchor="middle" font-size="12" font-weight="700" fill="{col}">{esc(d["name"])}</text>')
        vtxt = f'{sol["vm"][b]:.3f} pu ∠ {sol["va"][b]:.1f}°' if on else "0.000 pu · DEAD"
        vc = (RED if sol and on and not 0.95 <= sol["vm"][b] <= 1.05 else (GRN if on else DEAD))
        g.append(f'<text x="{x}" y="{y-18 if b in (1, 2, 4) else y+74}" text-anchor="middle" font-size="11" fill="{vc}">{vtxt}</text>')
        if d["kind"] in ("slack", "pv"):
            if b == 4:      # solar plant sits to the right of its bus, clear of the lines below
                gx, gy = x + 108, y
                g.append(f'<line x1="{x+52}" y1="{y}" x2="{gx-18}" y2="{gy}" stroke="{barc}" stroke-width="2.5"/>')
            else:
                gx, gy = x, y + 46
                g.append(f'<line x1="{x}" y1="{y+4}" x2="{x}" y2="{gy-18}" stroke="{barc}" stroke-width="2.5"/>')
            x = gx
            g.append(f'<circle cx="{x}" cy="{gy}" r="18" fill="{PANEL}" stroke="{barc}" stroke-width="2.5"/>')
            if b == 4:   # sun symbol for the solar plant
                g.append(f'<circle cx="{x}" cy="{gy}" r="6" fill="{barc}"/>')
                for k in range(8):
                    a = k * math.pi / 4
                    g.append(f'<line x1="{x+9*math.cos(a):.1f}" y1="{gy+9*math.sin(a):.1f}" x2="{x+13*math.cos(a):.1f}" y2="{gy+13*math.sin(a):.1f}" stroke="{barc}" stroke-width="1.8"/>')
            else:
                g.append(f'<path d="M{x-10},{gy} q5,-10 10,0 q5,10 10,0" fill="none" stroke="{barc}" stroke-width="2.5"/>')
            if sol and b in sol["gen"]:
                p, q = sol["gen"][b]
                gt = f"{p:.0f} MW · {q:+.0f} MVAr"
            else:
                gt = "OFFLINE"
            g.append(f'<text x="{x}" y="{gy+34}" text-anchor="middle" font-size="11" fill="{YEL if on else DEAD}">{gt}</text>')
            if b == 4:
                g.append(f'<text x="{x}" y="{gy+48}" text-anchor="middle" font-size="9.5" fill="{DIM}">driven by live Dhaka irradiance</text>')
        x = d["x"]
        if d["pl"] > 0:
            ly = y + 8 if b in (2,) else y - 8
            dirn = 1 if b == 2 else -1
            tip = y + dirn * 40
            g.append(f'<line x1="{x+38}" y1="{ly}" x2="{x+38}" y2="{tip}" stroke="{col}" stroke-width="2"/>'
                     f'<path d="M{x+32},{tip} L{x+44},{tip} L{x+38},{tip+dirn*10} Z" fill="{col}"/>'
                     f'<text x="{x+50}" y="{tip+dirn*4+4}" font-size="10.5" fill="{col}">{d["pl"]} MW</text>')

    # status strip
    total_load = sum(d["pl"] for d in BUSES.values())
    served = sum(BUSES[b]["pl"] for b in live)
    g.append(f'<line x1="16" y1="486" x2="{w-16}" y2="486" stroke="{EDGE}"/>')
    stats = [("LOAD SERVED", f"{served}/{total_load} MW", GRN if served == total_load else RED),
             ("LOSSES", f"{sol['losses']:.1f} MW" if sol else "—", TXT),
             ("SOLAR G2", f"{state.get('solar_mw', 0):.0f} MW", YEL),
             ("OPERATIONS", str(state["ops"]), TXT),
             ("RELAY TRIPS", str(state["trips"]), AMB),
             ("BLACKOUTS", str(state["collapses"]), RED)]
    for i, (k, v, c) in enumerate(stats):
        x = 30 + i * 160
        g.append(f'<text x="{x}" y="508" font-size="10" fill="{DIM}" letter-spacing="1.5">{k}</text>'
                 f'<text x="{x}" y="530" font-size="17" font-weight="700" fill="{c}">{esc(v)}</text>')
    al = alarms(sol)
    if al:
        txt = "  ·  ".join(al[:3])
        g.append(f'<circle cx="34" cy="560" r="5" fill="{RED}"><animate attributeName="opacity" values="1;.2;1" dur="1s" repeatCount="indefinite"/></circle>'
                 f'<text x="48" y="564" font-size="11.5" fill="{RED}">{esc(txt)}</text>')
    else:
        g.append(f'<circle cx="34" cy="560" r="5" fill="{GRN}"/><text x="48" y="564" font-size="11.5" fill="{GRN}">ALL CLEAR · voltages 0.95–1.05 pu · no overloads</text>')
    last = state["log"][0] if state["log"] else None
    lt = (f"last op: @{last['user']} · {last['action']} · {last['time']}" if last
          else f"updated {state.get('updated') or ''}")
    g.append(f'<text x="{w-30}" y="586" text-anchor="end" font-size="10.5" fill="{DIM}">{esc(lt)}</text>')
    g.append('</svg>')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(g) + "\n")


def render_svg(state):
    for theme, pal in THEMES.items():
        globals().update(pal)
        _render_svg(state, SVG.format(theme=theme))


# ----------------------------------------------------------------------------- README block
def issue_link(title):
    from urllib.parse import quote
    body = ("Press **Submit new issue** to send this switching order to the grid. "
            "A bot will run a Newton-Raphson power flow and reply in about a minute.")
    return f"https://github.com/{REPO}/issues/new?title={quote(title)}&body={quote(body)}"


def readme_block(state):
    sol = state["solution"]
    v = state["ops"]
    rows = []
    for cb, (f, t, *_r, rating) in LINES.items():
        st = "🟥 CLOSED" if state["closed"][cb] else "🟩 OPEN"
        fl = sol["flows"].get(cb) if sol else None
        load = f"{fl['loading']*100:.0f}%" if fl else "—"
        act = "Open it" if state["closed"][cb] else "Close it"
        rows.append(f"| **{cb}** | Bus {f} ↔ Bus {t} | {rating} MVA | {load} | {st} | [⚡ {act}]({issue_link('grid|toggle|' + cb)}) |")
    lb = sorted(state["operators"].items(), key=lambda kv: -kv[1])[:5]
    lead = " · ".join(f"[@{u}](https://github.com/{u}) ({n})" for u, n in lb) or "_nobody yet: be the first operator_"
    log = "\n".join(f"| {e['time']} | [@{e['user']}](https://github.com/{e['user']}) | `{e['action']}` | {e['result']} |"
                    for e in state["log"][:5]) or "| — | — | — | — |"
    return f"""<!--LIVEGRID:START-->
<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/live-grid-dark.svg?v={v}">
  <img src="assets/live-grid-light.svg?v={v}" width="100%" alt="Live 6-bus grid with current power flows, voltages and alarms"/>
</picture>
</p>

| Breaker | Line | Rating | Loading | State | Operate |
|:--:|:--:|:--:|:--:|:--:|:--:|
{chr(10).join(rows)}

<sub>🔁 [Black-start: close every breaker]({issue_link('grid|restore')}) · relays trip any line above {int(TRIP_AT*100)}% · a diverging power flow means a blackout</sub>

**Top operators:** {lead}

| Time (Dhaka) | Operator | Order | Grid response |
|---|---|---|---|
{log}
<!--LIVEGRID:END-->"""


def update_readme(state):
    with open(README, encoding="utf-8") as f:
        s = f.read()
    new = re.sub(r"<!--LIVEGRID:START-->.*?<!--LIVEGRID:END-->", lambda m: readme_block(state), s, flags=re.S)
    with open(README, "w", encoding="utf-8") as f:
        f.write(new)


# ----------------------------------------------------------------------------- main
CMD = re.compile(r"^grid\|(?:toggle\|(CB[1-8])|(restore))$")
USER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


def run(title, user, now):
    state = load_state()
    p_solar, fresh = solar_mw(now)
    state["solar_mw"] = p_solar
    stamp = now.strftime("%Y-%m-%d %H:%M")
    reply = []
    if title is not None:
        m = CMD.match(title.strip())
        if not m or not USER.match(user or ""):
            return state, None, ("⚠️ The grid bot did not recognise that order. Use the **⚡ Open it / Close it** links "
                                 "in the profile README; they fill in the title for you.")
        if m.group(1):
            cb = m.group(1)
            state["closed"][cb] = not state["closed"][cb]
            action = f"{'CLOSE' if state['closed'][cb] else 'OPEN'} {cb}"
        else:
            state["closed"] = {k: True for k in LINES}
            action = "BLACK-START"
        state["ops"] += 1
        state["operators"][user] = state["operators"].get(user, 0) + 1
    else:
        action, user = "SOLAR REFRESH", "grid-bot"

    sol, events = simulate(state["closed"], p_solar)
    trips = [e for e in events if e[0] == "TRIP"]
    state["trips"] += len(trips)
    if sol is None:
        state["collapses"] += 1
        state["closed"] = {k: True for k in LINES}       # black start
        sol, _ = simulate(state["closed"], p_solar)
        result = "💥 BLACKOUT, black-started"
        reply.append("## 💥 Blackout\n")
        reply += [f"- {msg}" for _, msg in events]
        reply.append("\nThe system collapsed, so the control room black-started it with every breaker closed. "
                     f"Total blackouts on this grid so far: **{state['collapses']}**.")
    else:
        al = alarms(sol)
        if trips:
            result = f"⚡ cascade: {len(trips)} relay trip(s)"
        elif al:
            result = "⚠️ " + al[0].lower()
        else:
            result = "✅ stable"
        reply.append(f"## ⚡ {action}: Newton-Raphson converged in {sol['iterations']} iteration{'s' if sol['iterations'] != 1 else ''}\n")
        if trips:
            reply.append("**Protection operated:**")
            reply += [f"- {msg}" for _, msg in trips]
            reply.append("")
        reply.append("| Bus | Voltage | Angle |\n|---|---|---|")
        reply += [f"| {BUSES[b]['name']} | {sol['vm'][b]:.4f} pu | {sol['va'][b]:.2f}° |" for b in sol["live"]]
        dead = [b for b in BUSES if b not in sol["live"]]
        if dead:
            reply.append("\nDe-energized: " + ", ".join(BUSES[b]["name"] for b in dead)
                         + f" ({sum(BUSES[b]['pl'] for b in dead)} MW unserved)")
        reply.append(f"\nLosses **{sol['losses']:.2f} MW** · Solar G2 **{p_solar:.0f} MW** "
                     f"({'today' if fresh else 'estimated'} Dhaka irradiance)")
        if al:
            reply.append("\n**Alarms:** " + " · ".join(al))
    state["solution"] = sol
    state["updated"] = stamp
    if title is not None:
        state["log"].insert(0, dict(time=stamp, user=user, action=action, result=result))
        state["log"] = state["log"][:20]
    reply.append(f"\n---\nThanks for operating the grid, @{user}! Your switching order is now on the "
                 f"[profile](https://github.com/{REPO.split('/')[0]}). 🔌")
    return state, f"⚡ live-grid: {action} by {user}", "\n".join(reply)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title"); ap.add_argument("--user")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--reply", default="reply.md"); ap.add_argument("--commit-msg", default="commit_msg.txt")
    ap.add_argument("--now", help="override time, ISO format (testing)")
    a = ap.parse_args()
    now = datetime.fromisoformat(a.now).replace(tzinfo=TZ) if a.now else datetime.now(TZ)
    state, msg, reply = run(None if a.refresh else a.title, a.user, now)
    with open(a.reply, "w", encoding="utf-8") as f:
        f.write(reply)
    if msg is None:
        print("invalid order, nothing changed"); return
    save_state(state); render_svg(state); update_readme(state)
    with open(a.commit_msg, "w") as f:
        f.write(msg + "\n")
    print(msg)


if __name__ == "__main__":
    main()
