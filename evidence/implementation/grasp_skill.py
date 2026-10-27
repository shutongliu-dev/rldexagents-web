"""Stateful Agent Skill API for the existing six-command Sharpa student."""

from copy import deepcopy
from threading import RLock
import time

import numpy as np

from .cluster_student import HandSample, REAL_LIMITS, TipFrameFK
from ..interaction.c0_command_student import (
    C0CommandRuntime, PHASES, real_hand_frame, sharpa_sdk_f6_to_policy,
)
from ..interaction.grasp_student import grasp_observation


class GraspSkill:
    """Three agent commands plus a host-owned 30 Hz measurement/control loop.

    `step_frame` and `step_real` return absolute joint targets and never send
    hardware commands. A new grasp selection clears history and requires an
    execute_phase call. Repeated identical commands leave duration/history intact.
    """

    def __init__(self, checkpoint, *, device="cpu", catalog=None,
                 joint_limits=None, auto_hold=True):
        self.policy = C0CommandRuntime(checkpoint, device=device)
        if self.policy.num_grasps != 6 or not self.policy.metadata.get("use_grasp_id", True):
            raise ValueError("GraspSkill requires the six-ID C0-C5 checkpoint")
        self.limits = np.array(REAL_LIMITS if joint_limits is None else joint_limits,
                               dtype=np.float32, copy=True)
        if self.limits.shape != (22, 2) or not np.isfinite(self.limits).all() or np.any(self.limits[:, 0] >= self.limits[:, 1]):
            raise ValueError("Expected finite ordered 22x2 joint limits")
        self.catalog = deepcopy(catalog or {})
        self.auto_hold = bool(auto_hold)
        self.threshold = float(self.policy.metadata.get("force_threshold_N") or 1.)
        self.dwell = int(self.policy.metadata.get("contact_dwell_steps") or 3)
        self.dt = float(self.policy.metadata["control_period_s"])
        self.lock = RLock()
        self.fk = None
        self.reset()

    @staticmethod
    def _id(value):
        if isinstance(value, str) and value in tuple(f"C{i}" for i in range(6)):
            return int(value[1])
        if type(value) is int and 0 <= value < 6:
            return value
        raise ValueError("grasp_id must be C0..C5 or an integer 0..5")

    def reset(self):
        with self.lock:
            self.policy.reset()
            self.grasp_id = None
            self.phase = None
            self.transition_reason = None
            self.form_steps = 0
            self.contact_streak = 0
            self.last_frame = None
            self.last_sample_time = None
            self.last_target = None
            self.target_clipped = False

    def set_grasp(self, grasp_id):
        index = self._id(grasp_id)
        with self.lock:
            if index != self.grasp_id:
                self.reset()
                self.grasp_id = index
            return self.get_status()

    def execute_phase(self, phase):
        if phase not in PHASES:
            raise ValueError("phase must be FORM, HOLD or RELEASE")
        with self.lock:
            if self.grasp_id is None:
                raise RuntimeError("Call set_grasp before execute_phase")
            if phase != self.phase:
                self.phase = phase
                self.transition_reason = "agent"
                self.contact_streak = 0
                self.form_steps = 0
                # Duration begins at the next control sample, including when
                # multiple phase commands arrive between two control ticks.
                self.policy.last_phase = None
            return self.get_status()

    def handle_command(self, command):
        """Accept {skill:grasp, grasp_id:C0, phase:FORM} or the three API calls."""
        if not isinstance(command, dict) or command.get("skill", "grasp") != "grasp":
            raise ValueError("Expected a grasp skill command")
        action = command.get("action")
        allowed = {None: {"skill", "grasp_id", "phase"},
                   "set_grasp": {"skill", "action", "grasp_id"},
                   "execute_phase": {"skill", "action", "phase"},
                   "get_status": {"skill", "action"}}
        if action not in allowed or set(command) - allowed[action]:
            raise ValueError("Unknown action or command fields")
        with self.lock:
            if action == "get_status":
                return self.get_status()
            if action == "set_grasp":
                return self.set_grasp(command["grasp_id"])
            if action == "execute_phase":
                return self.execute_phase(command["phase"])
            # Validate the complete command before changing either selection.
            index = self._id(command.get("grasp_id"))
            if command.get("phase") not in PHASES:
                raise ValueError("phase must be FORM, HOLD or RELEASE")
            self.set_grasp(index)
            return self.execute_phase(command["phase"])

    def step_frame(self, measured_frame, *, now_s=None):
        """Host loop: one current 107D (or raw simulator 113D) frame per tick.

        History, command one-hots, duration, previous raw action, decode and
        EMA are handled internally. Apply the returned radians WITHOUT another
        EMA. Simulator callers may pass its joint limits at construction.
        """
        frame = grasp_observation(np.asarray(measured_frame, np.float32), 107).copy()
        now = time.monotonic() if now_s is None else float(now_s)
        if frame.shape != (107,) or not np.isfinite(frame).all() or not np.isfinite(now):
            raise ValueError("Expected finite measured frame and timestamp")
        if not np.isin(frame[102:107], [0., 1.]).all():
            raise ValueError("Force valid flags must be binary")
        with self.lock:
            if self.grasp_id is None or self.phase is None:
                raise RuntimeError("Call set_grasp and execute_phase before stepping")
            if self.last_sample_time is not None and now <= self.last_sample_time:
                raise ValueError("Control samples must have increasing timestamps")
            force = np.linalg.norm(frame[87:102].reshape(5, 3) * 10, axis=-1)
            two = ((force >= self.threshold) & (frame[102:107] > .5)).sum() >= 2
            if self.phase == "FORM":
                # Match the original adapter: ignore contact for the first
                # 30 control samples while the external wrist waits.
                if self.form_steps >= 30:
                    self.contact_streak = self.contact_streak + 1 if two else 0
                    if self.auto_hold and self.contact_streak >= self.dwell:
                        self.phase = "HOLD"
                        self.transition_reason = "two_valid_fingertips"
                self.form_steps += 1
            target = self.policy.step(frame, self.grasp_id, self.phase)
            bounded = np.clip(target, self.limits[:, 0], self.limits[:, 1]).astype(np.float32)
            if np.max(np.abs(bounded - frame[:22])) > 1.5:
                raise ValueError("Clamped target exceeds 1.5 rad from measured joints")
            self.target_clipped = bool(np.any(bounded != target))
            self.policy.previous_target = bounded.copy()
            self.last_target = bounded.copy()
            self.last_frame = frame
            self.last_sample_time = now
            return bounded

    def step_real(self, sample: HandSample, *, now_s=None):
        """Timestamped SDK measurements; retains existing deploy freshness limits."""
        now = time.monotonic() if now_s is None else float(now_s)
        times = np.asarray(sample.tactile_time_s, dtype=np.float64)
        if not np.isfinite([now, sample.hand_time_s, sample.wrist_time_s]).all():
            raise ValueError("Expected finite hand, wrist and current timestamps")
        if not 0 <= now - sample.hand_time_s <= .25 or not 0 <= now - sample.wrist_time_s <= .25:
            raise ValueError("Hand/wrist state is stale or timestamp is in the future")
        if times.shape != (5,) or not np.isfinite(times).all() or np.any((now-times < 0) | (now-times > 1.)):
            raise ValueError("Tactile channels are stale or timestamps are invalid")
        with self.lock:
            if self.fk is None:
                self.fk = TipFrameFK()
            frame = real_hand_frame(sample.q_rad, sample.dq_rad_s, sample.palm_twist,
                                    sharpa_sdk_f6_to_policy(sample.sdk_f6_xyz_N),
                                    self.fk.rotations(sample.q_rad), np.ones(5, bool))
            return self.step_frame(frame, now_s=now)

    def get_status(self, *, now_s=None):
        with self.lock:
            now = time.monotonic() if now_s is None else float(now_s)
            frame = self.last_frame
            valid = None if frame is None else frame[102:107].astype(bool)
            force = None if frame is None else frame[87:102].reshape(5, 3)*10
            contact = None if force is None else ((np.linalg.norm(force, axis=-1) >= self.threshold) & valid)
            duration = (self.policy.phase_ticks*self.dt
                        if self.phase is not None and self.policy.last_phase == PHASES.index(self.phase) else 0.)
            return {
                "skill": "grasp", "grasp_id": None if self.grasp_id is None else f"C{self.grasp_id}",
                "phase": self.phase, "transition_reason": self.transition_reason,
                "phase_duration_s": duration,
                "control_period_s": self.dt,
                "sample_age_s": None if frame is None else now-self.last_sample_time,
                "measurement_stale": frame is None or now-self.last_sample_time > .25,
                "q_rad": None if frame is None else frame[:22].tolist(),
                "dq_rad_s": None if frame is None else frame[22:44].tolist(),
                "tip_force_local_N": None if frame is None else (frame[72:87].reshape(5, 3)*10).tolist(),
                "tip_force_palm_N": None if force is None else force.tolist(),
                "force_valid": None if valid is None else valid.tolist(),
                "contact_estimate": None if contact is None else {
                    "fingers": contact.tolist(), "two_tip_contact": bool(contact.sum() >= 2),
                    "threshold_N": self.threshold, "consecutive_form_steps": self.contact_streak,
                    "meaning": "Measured fingertip load; partner and non-tip contacts are unknown",
                },
                "grasp_success": None,
                "target_q_rad": None if self.last_target is None else self.last_target.tolist(),
                "target_clipped": self.target_clipped,
                "support": deepcopy(self.catalog.get("grasps", {}).get(f"C{self.grasp_id}")),
            }
