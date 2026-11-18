"""Demo: adaptive controller vs fixed-rate sender on a 10 Mbps link."""

from qos_control import AdaptiveController, LinkConfig, run_simulation


def show(label: str, result) -> None:
    m = result.metrics
    print(f"{label}")
    print(f"  throughput: {m.throughput_mbps:.2f} Mbps")
    print(f"  average delay: {m.avg_delay_ms:.1f} ms (max {m.max_delay_ms:.1f} ms)")
    print(f"  loss ratio: {m.loss_ratio:.4f}")
    print(f"  average queue: {m.avg_queue_packets:.1f} packets")


def main() -> None:
    config = LinkConfig(bandwidth_mbps=10, queue_packets=50, base_rtt_ms=20.0)

    adaptive = run_simulation(
        config, duration_s=10.0, controller=AdaptiveController(initial_rate_mbps=5.0)
    )
    show("Adaptive controller:", adaptive)

    fixed = run_simulation(config, duration_s=10.0, fixed_rate_mbps=20.0)
    show("Fixed 20 Mbps sender (overloads the 10 Mbps link):", fixed)


if __name__ == "__main__":
    main()
