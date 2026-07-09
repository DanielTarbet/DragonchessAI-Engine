#!/usr/bin/env python3
"""
Round-robin tournament between the bundled Dragonchess agents.

All searching agents use the same alpha-beta depth, so the evaluation function
is the only thing that varies. Each pair plays an equal number of games as Gold
and as Scarlet to cancel first-move advantage. Reports win/loss/draw, score, and
Bradley-Terry Elo, plus head-to-head confidence intervals.

Requires the headless engine built at ../build-headless/dragonchess and the CSV
weight files in ../weights/. See the top-level README for build instructions.
"""
from __future__ import annotations
import argparse, itertools, json, math, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "build-headless" / "dragonchess"
WDIR = ROOT / "weights"

WIN_RE = re.compile(r"Gold wins:\s+(\d+).*?Scarlet wins:\s+(\d+).*?Draws:\s+(\d+)", re.S)


def load_csv(name):
    return [float(x) for x in (WDIR / name).read_text().strip().split(",")]


def agents():
    return {
        "TD-lambda": {"ai": "tdeval",    "weights": load_csv("td_lambda.csv"), "depth": 2},
        "CMA-ES":    {"ai": "evolvable", "weights": load_csv("cma_es.csv"),    "depth": 2},
        "Jackman":   {"ai": "evolvable", "weights": load_csv("jackman.csv"),   "depth": 2},
        "AlphaBeta": {"ai": "alphabeta", "weights": None,                      "depth": 2},
        "Random":    {"ai": "random",    "weights": None,                      "depth": 0},
    }


def role_args(role, spec):
    ai, d, w = spec["ai"], spec["depth"], spec["weights"]
    a = [f"--{role}-ai", ai]
    if ai == "tdeval":
        a += [f"--{role}-td-weights", ",".join(map(str, w)), "--td-depth", str(d)]
    elif ai == "evolvable":
        a += [f"--{role}-weights", ",".join(map(str, w)), f"--{role}-depth", str(d)]
    elif ai in ("alphabeta", "minimax"):
        a += [f"--{role}-depth", str(d)]
    return a


def play(gold, scarlet, A, games, threads):
    cmd = [str(BIN), "--headless", "--mode", "tournament",
           "--games", str(games), "--threads", str(threads)]
    cmd += role_args("gold", A[gold]) + role_args("scarlet", A[scarlet])
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=7200).stdout
    m = WIN_RE.search(out)
    if not m:
        sys.exit(f"could not parse engine output for {gold} vs {scarlet}:\n{out}")
    return tuple(int(x) for x in m.groups())  # gold_w, scarlet_w, draws


def bt_elo(pair_scores, names, anchor=1500.0, scale=400.0, iters=10000, lr=0.02):
    r = {n: 0.0 for n in names}
    for _ in range(iters):
        grad = {n: 0.0 for n in names}
        for (a, b), (s_a, g) in pair_scores.items():
            if not g:
                continue
            p = 1.0 / (1.0 + 10.0 ** (-(r[a] - r[b]) / scale))
            e = (s_a / g) - p
            grad[a] += e * g; grad[b] -= e * g
        for n in names:
            r[n] += lr * grad[n]
        m = sum(r.values()) / len(r)
        for n in names:
            r[n] -= m
    return {n: anchor + r[n] for n in names}


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n; den = 1 + z*z/n
    c = (p + z*z/(2*n)) / den
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return (c - h, c + h)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--games", type=int, default=200, help="games per pair (split across colors)")
    ap.add_argument("--depth", type=int, default=None, help="override depth for all searching agents")
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=str(ROOT / "tournament_results.json"))
    args = ap.parse_args()

    if not BIN.exists():
        sys.exit(f"engine not found at {BIN}\nBuild it first:\n"
                 f"  cmake -S . -B build-headless -DCMAKE_BUILD_TYPE=Release -DHEADLESS_ONLY=ON\n"
                 f"  cmake --build build-headless --parallel")

    A = agents()
    if args.depth is not None:
        for s in A.values():
            if s["ai"] != "random":
                s["depth"] = args.depth
    names = list(A)
    half = args.games // 2
    tally = {n: {"W": 0, "L": 0, "D": 0} for n in names}
    pair_scores, pair_detail = {}, {}

    for a, b in itertools.combinations(names, 2):
        gw1, sw1, d1 = play(a, b, A, half, args.threads)
        gw2, sw2, d2 = play(b, a, A, half, args.threads)
        aw, bw, dr = gw1 + sw2, sw1 + gw2, d1 + d2
        g = aw + bw + dr
        tally[a]["W"] += aw; tally[a]["L"] += bw; tally[a]["D"] += dr
        tally[b]["W"] += bw; tally[b]["L"] += aw; tally[b]["D"] += dr
        pair_scores[(a, b)] = (aw + 0.5 * dr, g)
        lo, hi = wilson(aw, aw + bw)
        pair_detail[f"{a}_vs_{b}"] = {"a_wins": aw, "b_wins": bw, "draws": dr,
                                      "a_rate_decisive": aw / (aw + bw) if (aw + bw) else None,
                                      "ci95": [lo, hi]}
        print(f"{a:10} vs {b:10}: {aw:4}-{bw:4}-{dr:4}", flush=True)

    elo = bt_elo(pair_scores, names)
    rows = []
    for n in names:
        t = tally[n]; tot = sum(t.values())
        rows.append({"agent": n, **t, "games": tot,
                     "score": (t["W"] + 0.5 * t["D"]) / tot, "elo": round(elo[n], 1)})
    rows.sort(key=lambda x: x["elo"], reverse=True)
    json.dump({"games_per_pair": args.games, "standings": rows, "pairwise": pair_detail},
              open(args.out, "w"), indent=2)

    print(f"\n{'Agent':10} {'W':>5} {'L':>5} {'D':>5} {'Score':>7} {'Elo':>8}")
    for r in rows:
        print(f"{r['agent']:10} {r['W']:>5} {r['L']:>5} {r['D']:>5} {r['score']:>7.3f} {r['elo']:>8.1f}")
    print(f"\nSaved {args.out}")


if __name__ == "__main__":
    main()
