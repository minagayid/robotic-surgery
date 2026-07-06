"""Layer 5 -- sim-to-real validation & safety (Section 5).

Never deploy retargeted human-video policies straight to hardware. Validate in
simulation first with domain randomization, then a staged real-world rollout
under conservative torque/force/speed limits, a human-supervised kill switch,
and success/failure logging that feeds back into the dataset.

* :mod:`~robotx.sim2real.safety`     -- limits, clamping, kill switch.
* :mod:`~robotx.sim2real.validation` -- sim validation harness + domain rand.
* :mod:`~robotx.sim2real.rollout`    -- staged real-world rollout + logging.
"""

from .rollout import RolloutLog, StagedRollout
from .safety import SafetyEnvelope, SafetyViolation
from .validation import SimValidator, ValidationReport

__all__ = [
    "SafetyEnvelope",
    "SafetyViolation",
    "SimValidator",
    "ValidationReport",
    "StagedRollout",
    "RolloutLog",
]
