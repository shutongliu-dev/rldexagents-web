"""Grasp command students with eight frames of local hand and force input."""

from collections import deque

import numpy as np
import torch
from torch import nn

from .grasp_student import grasp_observation
from dexhand_hoi_learning.robots.constants import HAND_JOINT_SUFFIXES


PHASES = ("FORM", "HOLD", "RELEASE")
FRAME_DIM = 107
HISTORY = 8


def sharpa_sdk_f6_to_policy(f6_xyz):
    """Map the release SDK channel order to thumb,index,middle,ring,pinky."""
    force = np.asarray(f6_xyz, np.float32)
    if force.shape != (5, 3) or not np.isfinite(force).all():
        raise ValueError("Expected five finite Sharpa F6 xyz vectors in SDK order")
    return force[::-1].copy()


def real_hand_frame(q_rad, dq_rad_s, palm_twist, tip_force_local_N,
                    tip_to_palm_rotation, force_valid):
    """Build the 107D policy frame from measured real-hand quantities.

    `tip_to_palm_rotation` is five 3x3 matrices from each elastomer frame to
    the palm frame. All finger values must already follow the checkpoint's
    `joint_names` order. The runtime fills the previous-action channels.
    """
    q = np.asarray(q_rad, np.float32)
    dq = np.asarray(dq_rad_s, np.float32)
    twist = np.asarray(palm_twist, np.float32)
    force = np.asarray(tip_force_local_N, np.float32)
    rotation = np.asarray(tip_to_palm_rotation, np.float32)
    valid = np.asarray(force_valid, bool)
    if (q.shape != (22,) or dq.shape != (22,) or twist.shape != (6,)
            or force.shape != (5, 3) or rotation.shape != (5, 3, 3)
            or valid.shape != (5,)):
        raise ValueError("Expected q22,dq22,palm twist6,force5x3,rotation5x3x3,valid5")
    if not all(np.isfinite(x).all() for x in (q, dq, twist, force, rotation)):
        raise ValueError("Real hand measurements must be finite")
    local = np.clip(np.where(valid[:, None], force, 0), -40, 40) / 10
    palm = np.clip(np.einsum("fij,fj->fi", rotation, force), -40, 40) / 10
    palm[~valid] = 0
    return np.concatenate((q, dq, np.zeros(22, np.float32), twist,
                           local.flatten(), palm.flatten(), valid.astype(np.float32)))


def command_one_hot(grasp_id, phase, age_s, *, device=None, include_grasp_id=True, num_grasps=5):
    grasp_id = torch.as_tensor(grasp_id, dtype=torch.long, device=device)
    phase = torch.as_tensor(phase, dtype=torch.long, device=device)
    age_s = torch.as_tensor(age_s, dtype=torch.float32, device=device)
    if grasp_id.shape != phase.shape or torch.any((grasp_id < 0) | (grasp_id >= num_grasps)):
        raise ValueError(f"grasp_id must be in [0,{num_grasps - 1}] and match phase shape")
    if torch.any((phase < 0) | (phase >= 3)):
        raise ValueError("phase must be FORM, HOLD or RELEASE")
    if age_s.shape != phase.shape or not torch.isfinite(age_s).all() or torch.any(age_s < 0):
        raise ValueError("age_s must be finite, nonnegative and match phase shape")
    grasp = torch.nn.functional.one_hot(grasp_id, num_grasps).float()
    if not include_grasp_id:
        grasp = torch.zeros_like(grasp)
    return torch.cat((grasp,
                      torch.nn.functional.one_hot(phase, 3),
                      age_s.clamp(max=5)[..., None] / 5), dim=-1).float()


class C0CommandStudent(nn.Module):
    def __init__(self, num_grasps=5):
        super().__init__()
        self.num_grasps = num_grasps
        self.frame = nn.Sequential(nn.Linear(FRAME_DIM + num_grasps + 4, 192), nn.ELU())
        self.history = nn.GRU(192, 192, batch_first=True)
        self.head = nn.Sequential(nn.Linear(192, 128), nn.ELU(), nn.Linear(128, 22), nn.Tanh())

    def forward(self, history):
        if history.shape[-2:] != (HISTORY, FRAME_DIM + self.num_grasps + 4):
            raise ValueError(f"Expected [batch,8,{FRAME_DIM + self.num_grasps + 4}] local hand/force/command history")
        _, hidden = self.history(self.frame(history))
        return self.head(hidden[-1])


class C0CommandRuntime:
    """Inference-only joint-target adapter; the arm/wrist is controlled externally."""

    def __init__(self, checkpoint, device="cpu"):
        saved = torch.load(checkpoint, map_location=device, weights_only=False)
        self.metadata = saved["metadata"]
        self.num_grasps = int(self.metadata.get("num_grasps", 5))
        self.model = C0CommandStudent(self.num_grasps).to(device)
        self.model.load_state_dict(saved["student_state_dict"])
        self.model.eval()
        expected = [f"right_{name}" for name in HAND_JOINT_SUFFIXES]
        if self.metadata["joint_names"] != expected:
            raise ValueError("Checkpoint joint order differs from the real Sharpa SDK order")
        self.device = device
        self.scale = torch.as_tensor(saved["action_scale"]).cpu().numpy().astype(np.float32)
        self.offset = torch.as_tensor(saved["action_offset"]).cpu().numpy().astype(np.float32)
        self.reset()

    def reset(self):
        self.rows = deque(maxlen=HISTORY)
        self.previous_action = np.zeros(22, dtype=np.float32)
        self.previous_target = None
        self.last_phase = None
        self.phase_ticks = 0

    @torch.no_grad()
    def step(self, measured_frame, grasp_id=None, phase="FORM"):
        """Return 22 joint targets in checkpoint joint order and radians.

        measured_frame is 107D local state: q22,dq22,previous-action22,
        palm twist6, tip-frame forces15, palm-frame forces15,valid5.
        A raw 113D simulation frame is also accepted and converted locally.
        """
        if isinstance(phase, str):
            phase = PHASES.index(phase)
        if grasp_id is None:
            if self.metadata.get("use_grasp_id", True):
                raise ValueError("This student requires a grasp ID")
            grasp_id = 0
        frame = grasp_observation(np.asarray(measured_frame, np.float32), FRAME_DIM).copy()
        if frame.shape != (FRAME_DIM,) or not np.isfinite(frame).all():
            raise ValueError("Expected one finite 107D hand/force frame")
        frame[44:66] = self.previous_action
        self.phase_ticks = self.phase_ticks + 1 if phase == self.last_phase else 0
        self.last_phase = phase
        command = command_one_hot(
            grasp_id, phase, self.phase_ticks * float(self.metadata["control_period_s"]),
            include_grasp_id=bool(self.metadata.get("use_grasp_id", True)), num_grasps=self.num_grasps,
        ).cpu().numpy()
        row = np.concatenate((frame, command))
        self.rows.append(row)
        history = np.stack([self.rows[0]] * (HISTORY - len(self.rows)) + list(self.rows))
        raw = self.model(torch.from_numpy(history[None]).to(self.device))[0].cpu().numpy()
        if phase == 2:
            # A RELEASE command has an exact actuator target. Use it directly:
            # the selected SONIC experts themselves sometimes leave the hand
            # partly closed after a short release segment.
            raw = np.clip(-self.offset / self.scale, -1, 1)
            nominal = np.zeros(22, np.float32)
        else:
            nominal = self.offset + self.scale * raw
        alpha = float(self.metadata["action_smoothing_alpha"])
        previous = frame[:22] if self.previous_target is None else self.previous_target
        target = alpha * nominal + (1 - alpha) * previous
        # The release runtime already rejects targets more than 1.5 rad from
        # measured joints. Apply the same bound before sending a command.
        if np.max(np.abs(target - frame[:22])) > 1.5:
            raise ValueError("Hand target exceeds 1.5 rad from measured q")
        if not np.isfinite(target).all():
            raise ValueError("Nonfinite hand target")
        self.previous_action = raw
        self.previous_target = target
        return target

    def step_real(self, q_rad, dq_rad_s, palm_twist, sdk_f6_xyz_N,
                  tip_to_palm_rotation, grasp_id=None, phase="FORM", *, now_s,
                  hand_time_s, tactile_time_s):
        """Timestamped Sharpa SDK input; returns SDK-order joint targets."""
        now = float(now_s)
        hand_time = float(hand_time_s)
        tactile_time = np.asarray(tactile_time_s, dtype=np.float64)
        if tactile_time.shape != (5,) or not np.isfinite(tactile_time).all():
            raise ValueError("Expected five finite tactile timestamps")
        if not np.isfinite([now, hand_time]).all():
            raise ValueError("Expected finite hand and current timestamps")
        if not (0 <= now - hand_time <= .25):
            raise ValueError("Hand state is stale or timestamp is in the future")
        age = now - tactile_time
        if np.any((age < 0) | (age > 1.0)):
            raise ValueError("One or more tactile channels are stale")
        frame = real_hand_frame(q_rad, dq_rad_s, palm_twist,
                                sharpa_sdk_f6_to_policy(sdk_f6_xyz_N),
                                tip_to_palm_rotation, np.ones(5, bool))
        return self.step(frame, grasp_id, phase)


class BinaryGraspRuntime:
    """Two-command interface for the CLOSE/OPEN grasp ablation."""

    def __init__(self, checkpoint, device="cpu"):
        self.policy = C0CommandRuntime(checkpoint, device=device)
        if self.policy.num_grasps != 1 or not self.policy.metadata.get("binary_command", False):
            raise ValueError("Expected a binary CLOSE/OPEN checkpoint")

    def reset(self):
        self.policy.reset()

    def step(self, measured_frame, command="CLOSE"):
        if command not in ("CLOSE", "OPEN"):
            raise ValueError("command must be CLOSE or OPEN")
        return self.policy.step(measured_frame, grasp_id=0,
                                phase="FORM" if command == "CLOSE" else "RELEASE")

    def step_real(self, q_rad, dq_rad_s, palm_twist, sdk_f6_xyz_N,
                  tip_to_palm_rotation, command="CLOSE", *, now_s,
                  hand_time_s, tactile_time_s):
        if command not in ("CLOSE", "OPEN"):
            raise ValueError("command must be CLOSE or OPEN")
        return self.policy.step_real(q_rad, dq_rad_s, palm_twist, sdk_f6_xyz_N,
                                     tip_to_palm_rotation, grasp_id=0,
                                     phase="FORM" if command == "CLOSE" else "RELEASE",
                                     now_s=now_s, hand_time_s=hand_time_s,
                                     tactile_time_s=tactile_time_s)
