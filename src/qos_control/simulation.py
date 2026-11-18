"""Run a link simulation with an adaptive or fixed-rate sender."""

from __future__ import annotations

from dataclasses import dataclass

from .controller import AdaptiveController
from .link import LinkConfig, LinkSimulator, StepResult
from .metrics import QoSMetrics, compute_qos


@dataclass(frozen=True)
class SimulationResult:
    """A completed simulation run."""

    steps: list[StepResult]
    rates_mbps: list[float]
    metrics: QoSMetrics


def run_simulation(
    config: LinkConfig,
    duration_s: float = 10.0,
    dt: float = 0.01,
    controller: AdaptiveController | None = None,
    fixed_rate_mbps: float | None = None,
) -> SimulationResult:
    """Simulate ``duration_s`` seconds on ``config``.

    Pass a controller for adaptive sending, or ``fixed_rate_mbps``
    for a constant sending rate. Exactly one of the two must be given.
    """
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    if dt <= 0:
        raise ValueError("dt must be positive")
    if (controller is None) == (fixed_rate_mbps is None):
        raise ValueError("pass exactly one of controller or fixed_rate_mbps")

    link = LinkSimulator(config)
    steps: list[StepResult] = []
    rates: list[float] = []
    n_steps = int(duration_s / dt)

    for _ in range(n_steps):
        if controller is not None:
            rate = controller.rate_mbps
        else:
            rate = float(fixed_rate_mbps)  # type: ignore[arg-type]
        result = link.step(rate, dt)
        steps.append(result)
        rates.append(rate)
        if controller is not None:
            controller.update(result.loss_ratio, result.rtt_ms)

    metrics = compute_qos(steps, dt, packet_size_bytes=config.packet_size_bytes)
    return SimulationResult(steps=steps, rates_mbps=rates, metrics=metrics)
