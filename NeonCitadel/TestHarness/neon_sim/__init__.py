"""
neon_sim — a headless, deterministic reference model of Neon Citadel's game
logic, used to validate the design *before* it runs on iOS.

This package deliberately contains NO hand-copied constants. Everything that
also lives in the Swift source (tunables, the level map) is parsed out of the
real .swift files by `spec.py`, so the tests fail loudly if the game and the
model drift apart.
"""
