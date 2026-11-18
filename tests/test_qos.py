import unittest

from qos_control import AdaptiveController, LinkConfig, LinkSimulator, compute_qos, run_simulation
from qos_control.link import StepResult


class TestLink(unittest.TestCase):
    def test_no_loss_below_capacity(self):
        link = LinkSimulator(LinkConfig(bandwidth_mbps=10, queue_packets=100))
        for _ in range(100):
            result = link.step(5.0, dt=0.01)
        self.assertEqual(result.lost_packets, 0.0)
        self.assertEqual(result.loss_ratio, 0.0)

    def test_loss_above_capacity_with_small_queue(self):
        link = LinkSimulator(LinkConfig(bandwidth_mbps=10, queue_packets=10))
        lost = 0.0
        for _ in range(200):
            result = link.step(50.0, dt=0.01)
            lost += result.lost_packets
        self.assertGreater(lost, 0.0)

    def test_delay_grows_with_queue(self):
        link = LinkSimulator(LinkConfig(bandwidth_mbps=10, queue_packets=100, base_rtt_ms=20.0))
        idle = link.step(0.0, dt=0.01)
        self.assertAlmostEqual(idle.rtt_ms, 20.0, places=6)
        link.step(50.0, dt=0.5)
        busy = link.step(50.0, dt=0.01)
        self.assertGreater(busy.rtt_ms, 20.0)

    def test_invalid_config_rejected(self):
        with self.assertRaises(ValueError):
            LinkConfig(bandwidth_mbps=0)
        with self.assertRaises(ValueError):
            LinkConfig(bandwidth_mbps=10, queue_packets=0)


class TestController(unittest.TestCase):
    def test_decreases_rate_on_high_loss(self):
        ctrl = AdaptiveController(initial_rate_mbps=10.0)
        new_rate = ctrl.update(loss_ratio=0.20, rtt_ms=30.0)
        self.assertLess(new_rate, 10.0)

    def test_increases_rate_on_low_loss_and_delay(self):
        ctrl = AdaptiveController(initial_rate_mbps=5.0)
        new_rate = ctrl.update(loss_ratio=0.0, rtt_ms=25.0)
        self.assertGreater(new_rate, 5.0)

    def test_rate_stays_within_bounds(self):
        ctrl = AdaptiveController(initial_rate_mbps=5.0, min_rate_mbps=1.0, max_rate_mbps=10.0)
        for _ in range(200):
            ctrl.update(loss_ratio=0.0, rtt_ms=25.0)
        self.assertLessEqual(ctrl.rate_mbps, 10.0)
        for _ in range(200):
            ctrl.update(loss_ratio=0.5, rtt_ms=500.0)
        self.assertGreaterEqual(ctrl.rate_mbps, 1.0)


class TestMetricsAndSimulation(unittest.TestCase):
    def test_qos_metrics(self):
        steps = [
            StepResult(sent_packets=10, delivered_packets=10, lost_packets=0, queue_packets=0, rtt_ms=20.0),
            StepResult(sent_packets=10, delivered_packets=8, lost_packets=2, queue_packets=5, rtt_ms=40.0),
        ]
        m = compute_qos(steps, dt=0.01)
        self.assertAlmostEqual(m.loss_ratio, 2 / 20, places=6)
        self.assertAlmostEqual(m.avg_delay_ms, 30.0, places=6)
        self.assertGreater(m.throughput_mbps, 0.0)

    def test_adaptive_beats_fixed_overload_on_loss(self):
        config = LinkConfig(bandwidth_mbps=10, queue_packets=50, base_rtt_ms=20.0)
        adaptive = run_simulation(config, duration_s=5.0, controller=AdaptiveController(initial_rate_mbps=5.0))
        fixed = run_simulation(config, duration_s=5.0, fixed_rate_mbps=30.0)
        self.assertLess(adaptive.metrics.loss_ratio, fixed.metrics.loss_ratio)
        # Adaptive should still use most of the link.
        self.assertGreater(adaptive.metrics.throughput_mbps, 5.0)

    def test_simulation_rejects_both_or_neither_sender(self):
        config = LinkConfig(bandwidth_mbps=10)
        with self.assertRaises(ValueError):
            run_simulation(config, duration_s=1.0)
        with self.assertRaises(ValueError):
            run_simulation(config, duration_s=1.0, controller=AdaptiveController(), fixed_rate_mbps=5.0)


if __name__ == "__main__":
    unittest.main()
