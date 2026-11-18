"""A bandwidth-constrained link simulator (pure Python, stdlib only).

Time advances in fixed steps. In each step the sender offers packets,
they join a finite queue (overflow is lost), and the link drains the
queue at its bandwidth. Packets left in the queue add delay.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LinkConfig:
    """Configuration for one constrained link."""

    bandwidth_mbps: float  # link capacity in megabits per second
    queue_packets: int = 100  # maximum queue length, in packets
    base_rtt_ms: float = 20.0  # round-trip time with an empty queue
    packet_size_bytes: int = 1500

    def __post_init__(self) -> None:
        if self.bandwidth_mbps <= 0:
            raise ValueError("bandwidth_mbps must be positive")
        if self.queue_packets <= 0:
            raise ValueError("queue_packets must be positive")
        if self.base_rtt_ms < 0:
            raise ValueError("base_rtt_ms must not be negative")
        if self.packet_size_bytes <= 0:
            raise ValueError("packet_size_bytes must be positive")

    @property
    def capacity_packets_per_sec(self) -> float:
        """Link capacity expressed in packets per second."""
        return self.bandwidth_mbps * 1_000_000 / 8 / self.packet_size_bytes


@dataclass(frozen=True)
class StepResult:
    """Outcome of one simulation step."""

    sent_packets: float
    delivered_packets: float
    lost_packets: float
    queue_packets: float
    rtt_ms: float

    @property
    def loss_ratio(self) -> float:
        if self.sent_packets <= 0:
            return 0.0
        return self.lost_packets / self.sent_packets


class LinkSimulator:
    """Simulates one link. State is the current queue length."""

    def __init__(self, config: LinkConfig) -> None:
        self.config = config
        self.queue: float = 0.0

    def reset(self) -> None:
        self.queue = 0.0

    def step(self, sending_rate_mbps: float, dt: float) -> StepResult:
        """Advance one step at ``sending_rate_mbps`` for ``dt`` seconds."""
        if sending_rate_mbps < 0:
            raise ValueError("sending_rate_mbps must not be negative")
        if dt <= 0:
            raise ValueError("dt must be positive")

        cfg = self.config
        sent = sending_rate_mbps * dt * 1_000_000 / 8 / cfg.packet_size_bytes

        # 1. Arrivals join the queue; overflow is lost.
        self.queue += sent
        lost = 0.0
        if self.queue > cfg.queue_packets:
            lost = self.queue - cfg.queue_packets
            self.queue = float(cfg.queue_packets)

        # 2. The link drains the queue at its capacity.
        service = cfg.capacity_packets_per_sec * dt
        delivered = min(self.queue, service)
        self.queue -= delivered

        # 3. Delay is base RTT plus queueing delay.
        queue_delay_ms = self.queue / cfg.capacity_packets_per_sec * 1000.0
        rtt_ms = cfg.base_rtt_ms + queue_delay_ms

        return StepResult(
            sent_packets=sent,
            delivered_packets=delivered,
            lost_packets=lost,
            queue_packets=self.queue,
            rtt_ms=rtt_ms,
        )
