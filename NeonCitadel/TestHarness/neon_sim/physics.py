"""
physics.py — a minimal fixed-timestep vertical integrator.

This mirrors how SpriteKit advances a dynamic body under constant gravity:
velocity and position are integrated semi-implicitly (Euler) each step. We use
it to reproduce the jump arc and confirm the measured apex matches the analytic
prediction from the parsed constants — i.e. that gravity and jumpVelocity are
mutually consistent and produce the intended "feel".
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JumpResult:
    apex_height: float       # max height above launch (points)
    time_to_apex: float      # seconds
    air_time: float          # seconds until returning to launch height
    samples: int


def simulate_jump(jump_velocity: float,
                  gravity_magnitude: float,
                  dt: float = 1.0 / 60.0,
                  max_seconds: float = 10.0) -> JumpResult:
    """Integrate a single jump from y=0 with initial upward velocity.

    Semi-implicit Euler: v += a*dt; y += v*dt — the same ordering SpriteKit
    uses, so the discrete apex lands a hair above the analytic value, which the
    tolerance in the tests accounts for.
    """
    y = 0.0
    v = jump_velocity
    g = -abs(gravity_magnitude)

    apex = 0.0
    t = 0.0
    t_apex = 0.0
    air_time = 0.0
    steps = 0
    max_steps = int(max_seconds / dt)

    while steps < max_steps:
        v += g * dt
        y += v * dt
        t += dt
        steps += 1

        if y > apex:
            apex = y
            t_apex = t

        # Came back down to (or below) launch height while descending.
        if y <= 0.0 and v < 0.0:
            air_time = t
            break

    return JumpResult(apex_height=apex, time_to_apex=t_apex,
                      air_time=air_time, samples=steps)


def horizontal_distance(move_speed: float, seconds: float) -> float:
    """Horizontal reach at full run speed over a span of time (points)."""
    return move_speed * seconds
