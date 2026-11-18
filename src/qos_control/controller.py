"""Adaptive sending-rate controller.

The controller keeps exponentially weighted moving averages (EWMAs) of
the observed loss ratio and round-trip time, then adjusts the sending
rate once per step:

- high loss or high delay  -> decrease the rate multiplicatively;
- low loss and low delay   -> increase the rate additively.

This is the classic AIMD shape, with the decrease sized by how bad
the observed loss / delay is — the adaptive, measurement-driven part
of the model.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AdaptiveController:
    """Adaptive controller for one sender."""

    initial_rate_mbps: float = 5.0
    min_rate_mbps: float = 0.5
    max_rate_mbps: float = 100.0
    target_loss: float = 0.02
    target_rtt_ms: float = 100.0
    ewma_alpha: float = 0.2  # weight given to the newest observation

    rate_mbps: float = field(init=False)
    ewma_loss: float = field(init=False, default=0.0)
    ewma_rtt_ms: float = field(init=False, default=0.0)
    steps: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        if self.initial_rate_mbps <= 0:
            raise ValueError("initial_rate_mbps must be positive")
        if not 0 < self.min_rate_mbps <= self.initial_rate_mbps <= self.max_rate_mbps:
            raise ValueError("require 0 < min_rate <= initial_rate <= max_rate")
        if not 0 <= self.target_loss < 1:
            raise ValueError("target_loss must be in [0, 1)")
        self.rate_mbps = self.initial_rate_mbps

    def update(self, loss_ratio: float, rtt_ms: float) -> float:
        """Observe one step and return the new sending rate (Mbps)."""
        if loss_ratio < 0 or loss_ratio > 1:
            raise ValueError("loss_ratio must be in [0, 1]")
        if rtt_ms < 0:
            raise ValueError("rtt_ms must not be negative")

        self.steps += 1
        if self.steps == 1:
            self.ewma_loss = loss_ratio
            self.ewma_rtt_ms = rtt_ms
        else:
            self.ewma_loss = (1 - self.ewma_alpha) * self.ewma_loss + self.ewma_alpha * loss_ratio
            self.ewma_rtt_ms = (1 - self.ewma_alpha) * self.ewma_rtt_ms + self.ewma_alpha * rtt_ms

        if self.ewma_loss > self.target_loss:
            # Multiplicative decrease, sized by the excess loss.
            decrease = 0.5 * min(1.0, self.ewma_loss / max(self.target_loss, 1e-9))
            self.rate_mbps *= max(0.5, 1.0 - decrease)
        elif self.ewma_rtt_ms > self.target_rtt_ms:
            # Delay is building up: back off, but less sharply.
            self.rate_mbps *= 0.9
        else:
            # Additive increase: probe for more bandwidth gently.
            self.rate_mbps += 0.5

        self.rate_mbps = max(self.min_rate_mbps, min(self.max_rate_mbps, self.rate_mbps))
        return self.rate_mbps

    def reset(self) -> None:
        self.rate_mbps = self.initial_rate_mbps
        self.ewma_loss = 0.0
        self.ewma_rtt_ms = 0.0
        self.steps = 0
