# Dragonchess Engine

A fast C++ engine for **Dragonchess**, the three-dimensional chess variant introduced
by Gary Gygax. Play is on three vertically stacked 12×8 boards (Sky, Ground, Underworld)
with fourteen piece types, inter-board movement, and ranged vertical abilities such as
the Dragon's strike and the Basilisk's freeze.

The engine provides alpha-beta search with a transposition table, several evaluation
agents (including learned and evolved evaluators), a headless mode for large-scale
self-play and tournaments, an SDL2 GUI for interactive play, and a plugin API for
dropping in your own AI.

## Build

Requires a C++17 compiler and CMake ≥ 3.15. The GUI additionally needs SDL2,
SDL2_image, and SDL2_ttf.

```bash
# Headless research binary (no GUI dependencies)
cmake -S . -B build-headless -DCMAKE_BUILD_TYPE=Release -DHEADLESS_ONLY=ON
cmake --build build-headless --parallel

# GUI binary
cmake -S . -B build-gui -DCMAKE_BUILD_TYPE=Release
cmake --build build-gui --parallel
```

Both produce a `dragonchess` executable in their build directory.

## Play (GUI)

```bash
./build-gui/dragonchess
```

Opens a windowed application with a menu to start a game, choose which agent controls
each side, and step through play across the three boards.

## Headless mode

The headless binary runs matches, tournaments, and self-play from the command line.

```bash
# One game, alpha-beta (depth 3) vs the greedy baseline
./build-headless/dragonchess --headless --mode match \
    --gold-ai alphabeta --gold-depth 3 --scarlet-ai greedyvalue

# 100-game head-to-head, multithreaded
./build-headless/dragonchess --headless --mode tournament --games 100 --threads 8 \
    --gold-ai alphabeta --gold-depth 2 --scarlet-ai minimax --scarlet-depth 2
```

**Agent types** (`--gold-ai` / `--scarlet-ai`):

| Type | Description |
|---|---|
| `random` | Uniform random legal move |
| `greedy` | Capture-focused |
| `greedyvalue` | Greedy with piece-value scoring |
| `minimax` | Minimax search (`--*-depth`) |
| `alphabeta` | Alpha-beta with transposition table (`--*-depth`) |
| `evolvable` | Linear material evaluation over 14 piece values (`--*-weights`) |
| `tdeval` | Linear evaluation over 40 features (`--*-td-weights`, `--td-depth`) |

Run `./build-headless/dragonchess --headless --help` for the full option list, including
CSV/JSON output and self-play NDJSON generation (`--mode selfplay`).

## Bundled agents

`weights/` ships three ready-to-use evaluators (see `weights/manifest.json` for the
piece ordering and provenance):

| File | Engine type | What it is |
|---|---|---|
| `td_lambda.csv` | `tdeval` (40) | Linear evaluation trained by self-play TD(λ) |
| `cma_es.csv` | `evolvable` (14) | Piece values evolved with CMA-ES |
| `jackman.csv` | `evolvable` (14) | Handcrafted Dragonchess piece values (Jackman, 1999) |

Example — the TD(λ) evaluator against the CMA-ES evaluator at equal search depth:

```bash
./build-headless/dragonchess --headless --mode tournament --games 100 --threads 8 \
    --gold-ai tdeval    --gold-td-weights   "$(cat weights/td_lambda.csv)" --td-depth 2 \
    --scarlet-ai evolvable --scarlet-weights "$(cat weights/cma_es.csv)"   --scarlet-depth 2
```

## Reproduce the agent comparison

`scripts/reproduce_tournament.py` runs a color-balanced round-robin between all bundled
agents plus `alphabeta` and `random` anchors, at a fixed search depth, and reports
win/loss/draw, score, and Bradley-Terry Elo with head-to-head confidence intervals.

```bash
python3 scripts/reproduce_tournament.py --games 1000   # ~6 min on 16 threads
```

Requires only Python 3 (standard library). Writes `tournament_results.json`.

## Custom AIs (plugins)

The engine can load an AI from a shared object at runtime
(`--gold-ai-plugin file.so`). See [docs/PLUGINS.md](docs/PLUGINS.md) and
[examples/example_bots.cpp](examples/example_bots.cpp) for the interface and a worked
example.

## Repository layout

```
src/            C++ engine (board, move generation, search, agents, GUI)
weights/        Bundled trained/evolved/handcrafted evaluators + manifest
scripts/        Reproduction tournament driver
examples/       Example AI plugin
docs/           Plugin API documentation
assets/         Piece art and fonts for the GUI
```

## Citation

This engine accompanies:

> J. O'Connor, A. Hoag, S. Goyette, and G. B. Parker. "Evolutionary Transfer
> Learning for Dragonchess." In *Proceedings of the 18th International Conference
> on Agents and Artificial Intelligence (ICAART)*, SciTePress, 2026.

```bibtex
@inproceedings{oconnor2026dragonchess,
  title     = {Evolutionary Transfer Learning for Dragonchess},
  author    = {O'Connor, Jim and Hoag, Annika and Goyette, Sarah and Parker, Gary B.},
  booktitle = {Proceedings of the 18th International Conference on Agents and
               Artificial Intelligence (ICAART)},
  publisher = {SciTePress},
  year      = {2026}
}
```

## License

See [LICENSE](LICENSE).
