"""QoS metrics computed from a list of simulation steps."""

from __future__ import annotations

from dataclasses import dataclass

from .link import StepResult


@dataclass(frozen=True)
class QoSMetrics:
    """Summary QoS metrics for one simulation run."""

    duration_s: float
    throughput_mbps: float
    avg_delay_ms: float
    max_delay_ms: float
    loss_ratio: float
    avg_queue_packets: float
    total_sent: float
    total_delivered: float
    total_lost: float


def compute_qos(results: list[StepResult], dt: float, packet_size_bytes: int = 1500) -> QoSMetrics:
    """Compute QoS metrics from step results taken every ``dt`` seconds."""
    if not results:
        raise ValueError("no step results to summarise")
    if dt <= 0:
        raise ValueError("dt must be positive")

    duration = len(results) * dt
    total_sent = sum(r.sent_packets for r in results)
    total_delivered = sum(r.delivered_packets for r in results)
    total_lost = sum(r.lost_packets for r in results)
    bits_delivered = total_delivered * packet_size_bytes * 8
    throughput = bits_delivered / duration / 1_000_000 if duration > 0 else 0.0

    return QoSMetrics(
        duration_s=duration,
        throughput_mbps=throughput,
        avg_delay_ms=sum(r.rtt_ms for r in results) / len(results),
        max_delay_ms=max(r.rtt_ms for r in results),
        loss_ratio=(total_lost / total_sent) if total_sent > 0 else 0.0,
        avg_queue_packets=sum(r.queue_packets for r in results) / len(results),
        total_sent=total_sent,
        total_delivered=total_delivered,
        total_lost=total_lost,
    )
