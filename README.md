# ML Congestion Control for QoS

Adaptive, machine-learning-style congestion control for QoS enhancement
in bandwidth-constrained communication networks.

This is an **original, independent implementation inspired by** the 2025
paper *“An Adaptive Optimized Machine Learning–Driven Congestion Control
Model for QoS Enhancement in Bandwidth-Constrained Communication
Networks”*. It is **not** the official code from that paper, and it does
not claim to reproduce its results. It implements the core idea in a
small, readable form: a sender observes loss and delay on a constrained
link and adapts its sending rate, so throughput stays high while delay
and loss stay low.

## What it does

- Simulates a bandwidth-constrained link with a finite queue, base
  latency, and packet loss on queue overflow (pure Python, standard
  library only — no network access and no external packages).
- Runs an adaptive controller that adjusts the sending rate from
  observed loss and round-trip time, in the spirit of AIMD with
  exponentially weighted moving averages.
- Reports QoS metrics for a run: throughput, average delay, packet
  loss ratio, and queue utilisation.
- Compares the adaptive controller against a fixed-rate sender in the
  demo, so the benefit is visible on the same link.
- Ships with a command-line tool and tests.

## Quick start

```bash
python3 -m pip install -e .
python3 examples/demo.py
```

### Command line

```bash
# Adaptive controller on a 10 Mbps link for 10 seconds
qos-control run --bandwidth 10 --duration 10

# Same link, fixed sending rate of 20 Mbps (overloads the link)
qos-control run --bandwidth 10 --duration 10 --fixed-rate 20

# Show the QoS metrics for a run
qos-control run --bandwidth 5 --duration 10 --queue 50 --base-rtt 20
```

## Project layout

```
src/qos_control/
  link.py        # LinkSimulator: bandwidth, queue, latency, loss
  controller.py  # AdaptiveController: rate adaptation from loss/delay
  metrics.py     # QoSMetrics: throughput, delay, loss
  simulation.py  # run_simulation(): link + controller over time
  cli.py         # Command-line interface
examples/
  demo.py
  sample_trace.csv
tests/
  test_qos.py
```

## How the simulator works

Time advances in fixed steps (default 0.01 s). In each step:

1. The sender offers packets at its current sending rate.
2. Packets join a finite queue; packets that do not fit are lost.
3. The link drains the queue at its bandwidth; packets left in the
   queue add delay.
4. Round-trip time is the base RTT plus queueing delay.

The controller updates once per step from the loss ratio and RTT
observed in that step:

- High loss or high delay → decrease the sending rate multiplicatively.
- Low loss and low delay → increase the sending rate additively.

This keeps the rate near the link capacity without filling the queue.

## Tests

```bash
python3 -m pytest -q
# or, without pytest:
python3 -m unittest discover -s tests -v
```

## Author

**Engr. Muhammad Awais Khan** — Bahauddin Zakariya University, Multan (Pakistan)

Google Scholar profile: https://scholar.google.com/citations?hl=en&user=c4UawvgAAAAJ

## Status

Experimental research code, version 0.1.0. It is a teaching and
prototyping simulator, not a production congestion-control
implementation, and it has not been validated against real network
measurements.

## License

MIT — see `LICENSE`.
