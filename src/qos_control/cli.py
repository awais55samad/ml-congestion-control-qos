"""Command-line interface: ``qos-control run``."""

from __future__ import annotations

import argparse
import sys

from .controller import AdaptiveController
from .link import LinkConfig
from .simulation import run_simulation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="qos-control",
        description="Adaptive congestion control simulation for QoS.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run a simulation and print QoS metrics")
    run.add_argument("--bandwidth", required=True, type=float, help="Link bandwidth in Mbps")
    run.add_argument("--duration", type=float, default=10.0, help="Simulation duration in seconds")
    run.add_argument("--queue", type=int, default=100, help="Queue size in packets")
    run.add_argument("--base-rtt", type=float, default=20.0, help="Base RTT in ms")
    run.add_argument("--initial-rate", type=float, default=5.0, help="Adaptive initial rate in Mbps")
    run.add_argument("--fixed-rate", type=float, default=None, help="Fixed sending rate in Mbps (instead of adaptive)")

    args = parser.parse_args(argv)
    try:
        config = LinkConfig(
            bandwidth_mbps=args.bandwidth,
            queue_packets=args.queue,
            base_rtt_ms=args.base_rtt,
        )
        if args.fixed_rate is not None:
            result = run_simulation(config, duration_s=args.duration, fixed_rate_mbps=args.fixed_rate)
            label = f"fixed rate {args.fixed_rate} Mbps"
        else:
            controller = AdaptiveController(initial_rate_mbps=args.initial_rate)
            result = run_simulation(config, duration_s=args.duration, controller=controller)
            label = f"adaptive (final rate {controller.rate_mbps:.2f} Mbps)"
        m = result.metrics
        print(f"{label} on a {args.bandwidth} Mbps link for {m.duration_s:.1f} s")
        print(f"throughput: {m.throughput_mbps:.2f} Mbps")
        print(f"average delay: {m.avg_delay_ms:.1f} ms (max {m.max_delay_ms:.1f} ms)")
        print(f"loss ratio: {m.loss_ratio:.4f}")
        print(f"average queue: {m.avg_queue_packets:.1f} packets")
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
