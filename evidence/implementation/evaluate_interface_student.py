"""Evaluate the link-near mixed-PPO student on its complete 2244-reference set.

The wrist follows each recorded HOI reference. The student receives only its
deployable H8x117 hand/tactile/cluster/phase input. This is a clean nominal
simulation evaluation; it does not measure arbitrary-object or real-robot success.
"""

import argparse
import json
import math
import os
from collections import Counter
from pathlib import Path

from isaaclab.app import AppLauncher

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--checkpoint', type=Path, required=True)
p.add_argument('--settings', type=Path, required=True)
p.add_argument('--references', type=Path, required=True)
p.add_argument('--cluster-ids', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--seed', type=int, default=42)
p.add_argument('--form-steps', type=int, default=30)
p.add_argument('--hold-extra-steps', type=int, default=30)
p.add_argument('--release-steps', type=int, default=30)
p.add_argument('--command-targets',type=Path,required=True)
p.add_argument('--teacher-model',type=Path)
AppLauncher.add_app_launcher_args(p)
p.set_defaults(headless=True)
a = p.parse_args()
if min(a.form_steps, a.hold_extra_steps, a.release_steps) < 0 or a.form_steps == 0:
    p.error('FORM must be positive; HOLD-extra and RELEASE lengths must be nonnegative')
paths = json.loads(a.references.read_text())
labels = json.loads(a.cluster_ids.read_text())
if not paths or len(labels) != len(paths):
    p.error('Expected the complete aligned 2244-reference final cluster selection')
if any(x not in range(6) for x in labels):p.error('Invalid cluster')
if a.output.exists():
    p.error('Choose a new evaluation output directory')

settings = json.loads(a.settings.read_text())
stage = dict(settings['stage'])
# Evaluate deployment behavior on nominal references; remove training-only DR.
stage.update(
    control_dr=False,
    control_dr_profile=None,
    action_delay_max_steps=0,
    real_hand_joint_limits=True,
    reference_random_start=False,
    reference_start_max_fraction=1.,
    initialization_curriculum_steps=0,
    initialization_curriculum_offset_steps=0,
    initialization_start_fraction=0.,
    open_hand_reset_probability=0.,
    open_hand_reset_pause_steps=0,
    object_reset_position_noise_m=0.,
    object_reset_yaw_noise_rad=0.,
    object_reset_noise_probability=1.,
    object_reset_noise_curriculum={},
    spatial_augmentation={'translation_m': [0., 0., 0.], 'yaw_rad': 0.},
    schedule_ratios=[1., 0., 0.],
    grasp_library=None,
)
stage['wrist_offset'] = {**stage.get('wrist_offset', {}), 'probability': 0.}
stage.pop('object_pose_dr', None)
stage.pop('object_mass_dr_kg', None)
stage.pop('dexcanvas_mass_dr_kg', None)
settings = dict(settings)
settings['stage'] = stage
settings.pop('object_pose_dr', None)
settings.pop('object_mass_dr_kg', None)
settings.pop('dexcanvas_mass_dr_kg', None)
os.environ['SHARPA_N_EPISODES']=str(len(paths))
os.environ['SHARPA_MIXED_REFERENCE_FILE'] = str(a.references.resolve())
os.environ['SHARPA_SEQUENCE_FILE'] = str(a.references.resolve())
os.environ['SHARPA_DATA_ROOT'] = '/data/spider_sharpa'
os.environ['SHARPA_WRIST_RANDOM'] = '0'
app = AppLauncher(a)
env = None
try:
    import numpy as np
    import torch
    import gymnasium as gym
    from isaaclab_tasks.utils import parse_env_cfg
    from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper
    import dexhand_hoi_learning.tasks  # noqa: F401
    from dexhand_hoi_learning.tasks.manager_based.sharpa_hand_local.contact_teacher import configure_contact_teacher
    from dexhand_hoi_learning.tasks.manager_based.sharpa_hand_local.tactile_pattern_teacher import tactile_actor_state
    from dexhand_hoi_learning.interaction.c0_command_student import C0CommandStudent, command_one_hot
    from dexhand_hoi_learning.interaction.grasp_student import grasp_observation
    from dexhand_hoi_learning.system0_v1.sonic_environment import configure_sonic
    from dexhand_hoi_learning.system0_v1.environment import _object_contact_by_finger, _contact
    from dexhand_hoi_learning.system0_v1.geometry import rotation_error
    from dexhand_hoi_learning.robots.constants import HAND_JOINT_SUFFIXES

    torch.set_num_threads(1)
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    cfg = parse_env_cfg('Sharpa-Hand-Local-v0', device=a.device, num_envs=len(paths))
    cfg.seed = a.seed
    configure_contact_teacher(cfg, None, settings['robot_usd'], settings, physical_reset=True)
    configure_sonic(cfg, stage)
    cfg.commands.reference.random_start = False
    for name in ('reference_done', 'time_out', 'dropped'):
        if hasattr(cfg.terminations, name):
            setattr(cfg.terminations, name, None)
    env = gym.make('Sharpa-Hand-Local-v0', cfg=cfg).unwrapped
    wrapped = RslRlVecEnvWrapper(env, clip_actions=1.)
    cmd = env.command_manager.get_term('reference')
    cmd.robot.write_joint_limits_to_sim(
        torch.tensor([[[-314.159, 314.159]] * 3], device=env.device)
        .expand(len(paths), -1, -1).contiguous(), joint_ids=cmd.wrist_ids[3:])
    expected_names = [f'right_{name}' for name in HAND_JOINT_SUFFIXES]
    saved = torch.load(a.checkpoint, map_location=env.device, weights_only=False)
    meta = saved['metadata']
    if meta.get('joint_names') != expected_names:
        raise ValueError('Checkpoint and simulator joint order differ')
    if int(meta.get('num_grasps', -1)) != 6:
        raise ValueError('Expected the six-class link-near student')
    from dexhand_hoi_learning.interaction.interface_student import InterfaceStudent,encode_command
    interface=meta['interface']
    model = InterfaceStudent(interface).to(env.device)
    model.load_state_dict(saved['student_state_dict'])
    model.eval()
    action_scale = torch.as_tensor(saved['action_scale'], device=env.device).float()
    action_offset = torch.as_tensor(saved['action_offset'], device=env.device).float()
    targets=json.loads(a.command_targets.read_text())
    if [r['reference'] for r in targets]!=paths:raise ValueError('Target ordering mismatch')
    q_seed=torch.tensor([r['q_seed'] for r in targets],device=env.device)
    tip_goal=torch.tensor([r['fingertips_palm_m'] for r in targets],device=env.device)
    if not torch.allclose(env.v1_fk(q_seed),tip_goal,atol=1e-5):raise ValueError('Target FK mismatch')
    def interface_command(cluster,phase,age,**kwargs):
        return encode_command(interface,cluster,q_seed,tip_goal,phase,age,action_scale,action_offset)

    if action_scale.shape != (22,) or action_offset.shape != (22,):
        raise ValueError('Expected 22D action scale and offset')
    bounds = cmd.robot.data.soft_joint_pos_limits[0, cmd.hand_ids]
    if getattr(env.cfg, 'v1_real_hand_joint_limits', False):
        bounds = env.v1_real_hand_bounds
    open_q = torch.zeros((len(paths), 22), device=env.device).clamp(bounds[:, 0], bounds[:, 1])
    open_action = ((open_q - action_offset) / action_scale.clamp_min(1e-6)).clamp(-1., 1.)
    if cmd.valid_steps.numel() != len(paths):
        raise ValueError('Loaded reference count differs from selection')
    loaded_keys = [json.loads(Path(path).read_text())['key'] for path in cmd.cfg.sequences]
    requested_keys = [json.loads(Path(path).read_text())['key'] for path in paths]
    if loaded_keys != requested_keys:
        raise ValueError('Loaded reference order differs from new cluster labels')

    device = env.device
    env_ids = torch.arange(len(paths), device=device)
    cmd.clock_paused = False
    wrapped.reset()
    cmd = env.command_manager.get_term('reference')
    cmd.robot.write_joint_state_to_sim(open_q, torch.zeros_like(open_q), joint_ids=cmd.hand_ids)
    env.action_manager.reset()
    env.sim.forward()
    env.scene.update(env.physics_dt)
    cmd.clock_paused = True
    env.v1_pattern_ids.fill_(0)
    env.v1_object_goal_valid = cmd.object_present.clone()
    env.v1_reset_generation += 1
    env.observation_manager.reset()

    frame = grasp_observation(tactile_actor_state(env).clone(), 107)
    phases = torch.zeros(len(paths), device=device, dtype=torch.long)
    cluster = torch.as_tensor(labels, device=device, dtype=torch.long)
    command = interface_command(cluster, phases, torch.zeros_like(phases, dtype=torch.float32),
                              device=device, num_grasps=6)
    history = torch.cat((frame, command), -1)[:, None, :].expand(-1, 8, -1).clone()
    phase_age = torch.zeros_like(phases)
    if a.teacher_model:
        import yaml
        from dexhand_hoi_learning.system0_v1.sonic_policy import SonicOnPolicyRunner
        runner=SonicOnPolicyRunner(wrapped,yaml.safe_load((a.teacher_model.parent/'params/agent.yaml').read_text()),log_dir=None,device=env.device)
        runner.load(str(a.teacher_model),load_optimizer=False)
        teacher_policy=runner.get_inference_policy(device=env.device)
        teacher_groups=wrapped.get_observations()
    horizons = cmd.valid_steps[env_ids] - 1
    episode_steps = horizons + a.form_steps + a.hold_extra_steps + a.release_steps
    max_steps = int(episode_steps.max().item())
    initial_obj = env.scene['object'].data.root_pos_w[:, :3] - env.scene.env_origins
    ref_start = cmd.ref_object_pos[cmd.env_episode, 0]
    ref_positions = cmd.ref_object_pos[cmd.env_episode]
    valid_ref = torch.arange(ref_positions.shape[1], device=device)[None, :] < cmd.valid_steps[:, None]
    reference_lift = (ref_positions[:, :, 2] - ref_start[:, None, 2]).masked_fill(~valid_ref, -torch.inf).amax(-1).clamp_min(0.)

    q_error_sum=torch.zeros(len(paths),device=device)
    tip_error_sum=torch.zeros_like(q_error_sum)
    hold_n = torch.zeros(len(paths), device=device)
    hold_pos_sum = torch.zeros_like(hold_n)
    hold_rot_sum = torch.zeros_like(hold_n)
    hold_pose_good = torch.zeros_like(hold_n)
    hold_contact = torch.zeros_like(hold_n)
    tail_n = torch.zeros_like(hold_n)
    tail_pos = torch.zeros_like(hold_n)
    tail_rot = torch.zeros_like(hold_n)
    tail_pose_good = torch.zeros_like(hold_n)
    tail_contact = torch.zeros_like(hold_n)
    release_n = torch.zeros_like(hold_n)
    release_free = torch.zeros_like(hold_n)
    release_q_sq = torch.zeros_like(hold_n)
    actual_lift = torch.zeros_like(hold_n)
    lift_contact_streak = torch.zeros_like(hold_n)
    lift_contact_streak_max = torch.zeros_like(hold_n)

    streams={k:[] for k in ('object_pose','hand_q','wrist_q','object_contact_N','tip_force_N','phase')}
    with torch.inference_mode():
        for tick in range(max_steps):
            cmd.clock_paused = tick < a.form_steps
            phase = torch.where(torch.full_like(cluster, tick) < a.form_steps, 0,
                     torch.where(tick >= a.form_steps + horizons + a.hold_extra_steps, 2, 1))
            phase_age=torch.where(phase==0,torch.full_like(cluster,tick),
                torch.where(phase==1,torch.full_like(cluster,tick-a.form_steps),tick-(a.form_steps+horizons+a.hold_extra_steps)))
            command = interface_command(cluster, phase, phase_age * float(env.step_dt),
                                      device=device, num_grasps=6)
            history[:, -1, 107:] = command
            action = (teacher_policy(teacher_groups) if a.teacher_model else model(history)).clamp(-1.,1.)
            if a.teacher_model:action=torch.where((phase==0)[:,None],open_action,action)
            action = torch.where((phase == 2)[:, None], open_action, action)
            next_groups, _, done, _ = wrapped.step(action)
            if a.teacher_model:teacher_groups=next_groups
            if done.any():
                raise RuntimeError('Unexpected auto-reset during fixed-reference evaluation')

            object_pos = env.scene['object'].data.root_pos_w[:, :3] - env.scene.env_origins
            object_q = env.scene['object'].data.root_quat_w[:, [1, 2, 3, 0]]
            ref_pos = cmd.object_reference_pos
            ref_q = cmd.object_reference_quat[:, [1, 2, 3, 0]]
            pos_err = (object_pos - ref_pos).norm(dim=-1)
            rot_err = rotation_error(object_q, ref_q)
            contacts = _object_contact_by_finger(env)
            n_contact = (contacts > .5).sum(-1)

            active = tick < episode_steps
            in_hold = active & (phase == 1)
            tail = in_hold & (tick >= a.form_steps + horizons + a.hold_extra_steps - 30)
            release = active & (phase == 2)
            hold_n += in_hold.float()
            hold_pos_sum += pos_err * in_hold
            hold_rot_sum += rot_err * in_hold
            hold_pose_good += ((pos_err <= .03) & (rot_err <= math.radians(30.)) & in_hold).float()
            hold_contact += ((n_contact >= 2) & in_hold).float()
            tail_n += tail.float()
            tail_pos += pos_err * tail
            tail_rot += rot_err * tail
            tail_pose_good += ((pos_err <= .03) & (rot_err <= math.radians(30.)) & tail).float()
            tail_contact += ((n_contact >= 2) & tail).float()
            release_n += release.float()
            release_free += ((n_contact == 0) & release).float()
            q_now = cmd.robot.data.joint_pos[:, cmd.hand_ids]
            q_error_sum+=(q_now-q_seed).abs().mean(-1)*in_hold
            tip_error_sum+=(env.v1_fk(q_now)-tip_goal).norm(dim=-1).mean(-1)*in_hold
            release_q_sq += ((q_now - open_q).square().mean(-1)) * release

            lift = object_pos[:, 2] - initial_obj[:, 2]
            actual_lift = torch.maximum(actual_lift, lift.clamp_min(0.))
            has_lift_contact = active & (lift >= .02) & (n_contact >= 2)
            lift_contact_streak = torch.where(has_lift_contact, lift_contact_streak + 1, 0.)
            lift_contact_streak_max = torch.maximum(lift_contact_streak_max, lift_contact_streak)

            for name,value in [('object_pose',torch.cat((object_pos,env.scene['object'].data.root_quat_w),-1)),
                               ('hand_q',q_now),('wrist_q',cmd.robot.data.joint_pos[:,cmd.wrist_ids]),
                               ('object_contact_N',contacts),('tip_force_N',_contact(env)),('phase',phase)]:
                streams[name].append(value.cpu().numpy().copy())
            next_frame = grasp_observation(tactile_actor_state(env).clone(), 107)
            next_frame[:, 44:66] = action
            next_phase = torch.where(torch.full_like(cluster, tick + 1) < a.form_steps, 0,
                          torch.where(tick + 1 >= a.form_steps + horizons + a.hold_extra_steps, 2, 1))
            next_age = torch.where(next_phase == phase, phase_age + 1, torch.zeros_like(phase_age))
            next_command = interface_command(cluster, next_phase, next_age * float(env.step_dt),
                                           device=device, num_grasps=6)
            history = torch.cat((history[:, 1:], torch.cat((next_frame, next_command), -1)[:, None, :]), dim=1)
            if (tick + 1) % 100 == 0 or tick + 1 == max_steps:
                print(f'eval tick {tick + 1}/{max_steps}', flush=True)

    hold_denom = hold_n.clamp_min(1.)
    tail_denom = tail_n.clamp_min(1.)
    release_denom = release_n.clamp_min(1.)
    arrays={k:np.stack(v) for k,v in streams.items()}
    a.output.mkdir(parents=True)
    from dexhand_hoi_learning.interaction.command_ablation_metrics import score_episode
    rows = []
    for i, path in enumerate(paths):
        descriptor = json.loads(Path(path).read_text())
        key = descriptor['key']
        cluster_id = int(labels[i])
        row = {
            'key': key, 'kind': descriptor['kind'], 'cluster_id': cluster_id,
            'interface':interface,'hold_q_goal_mae_rad':float(q_error_sum[i]/hold_denom[i]),
            'hold_tip_goal_error_m':float(tip_error_sum[i]/hold_denom[i]),
            'object_model_id': descriptor.get('object_model_id'),
            'reference_lift_m': float(reference_lift[i].item()),
            'actual_lift_m': float(actual_lift[i].item()),
            'hold_steps': int(hold_n[i].item()),
            'hold_position_mean_cm': float((hold_pos_sum[i] / hold_denom[i] * 100).item()),
            'hold_rotation_mean_deg': float((hold_rot_sum[i] / hold_denom[i] * 180 / math.pi).item()),
            'hold_pose_in_3cm_30deg_fraction': float((hold_pose_good[i] / hold_denom[i]).item()),
            'hold_two_finger_object_contact_fraction': float((hold_contact[i] / hold_denom[i]).item()),
            'tail_position_mean_cm': float((tail_pos[i] / tail_denom[i] * 100).item()),
            'tail_rotation_mean_deg': float((tail_rot[i] / tail_denom[i] * 180 / math.pi).item()),
            'tail_pose_in_3cm_30deg_fraction': float((tail_pose_good[i] / tail_denom[i]).item()),
            'tail_two_finger_object_contact_fraction': float((tail_contact[i] / tail_denom[i]).item()),
            'release_contact_free_fraction': float((release_free[i] / release_denom[i]).item()),
            'release_open_joint_rmse_rad': float(torch.sqrt(release_q_sq[i] / release_denom[i]).item()),
            'max_two_finger_lift_contact_steps': int(lift_contact_streak_max[i].item()),
            'lift_with_two_finger_contact_0_5s': bool(lift_contact_streak_max[i].item() * env.step_dt >= .5),
            'finite': bool(all(torch.isfinite(x).item() for x in (
                hold_pos_sum[i], hold_rot_sum[i], tail_pos[i], tail_rot[i], actual_lift[i]
            ))),
        }
        end=int(episode_steps[i]);one={k:v[:end,i] for k,v in arrays.items()};one['initial_z']=float(initial_obj[i,2])
        physical=score_episode(one,float(env.step_dt),int(a.form_steps+horizons[i]),int(a.form_steps+horizons[i]+a.hold_extra_steps))
        row.update(physical)
        np.savez_compressed(a.output/f'rollout_{i:04d}.npz',**one)
        rows.append(row)

    def aggregate(selected):
        if not selected:
            return {'episodes': 0}
        keys_num = ('hold_q_goal_mae_rad','hold_tip_goal_error_m','reference_lift_m', 'actual_lift_m', 'hold_position_mean_cm',
                    'hold_rotation_mean_deg', 'hold_pose_in_3cm_30deg_fraction',
                    'hold_two_finger_object_contact_fraction', 'tail_position_mean_cm',
                    'tail_rotation_mean_deg', 'tail_pose_in_3cm_30deg_fraction',
                    'tail_two_finger_object_contact_fraction', 'release_contact_free_fraction',
                    'release_open_joint_rmse_rad')
        out = {'episodes': len(selected), 'finite': sum(r['finite'] for r in selected)}
        for key in keys_num:
            out[key + '_mean'] = float(np.mean([r[key] for r in selected]))
            out[key + '_median'] = float(np.median([r[key] for r in selected]))
        for metric in ['lift_success','hold_1s_success','hold_5s_success','drop_after_lift']:
            out[metric]=sum(r[metric] for r in selected)
        out['force_over_20N_fraction_mean']=float(np.mean([r['force_over_20N_fraction'] for r in selected]))
        out['lift_with_two_finger_contact_0_5s'] = sum(r['lift_with_two_finger_contact_0_5s'] for r in selected)
        out['references_with_lift_target_ge_2cm'] = sum(r['reference_lift_m'] >= .02 for r in selected)
        out['tail_hold_pose_success'] = sum(
            r['tail_pose_in_3cm_30deg_fraction'] >= .8
            and r['tail_two_finger_object_contact_fraction'] >= .5 for r in selected)
        return out

    summary = {'overall': aggregate(rows), 'by_cluster': {}, 'by_kind': {}}
    for cid in range(6):
        summary['by_cluster'][str(cid)] = aggregate([r for r in rows if r['cluster_id'] == cid])
    for kind in sorted({r['kind'] for r in rows}):
        summary['by_kind'][kind] = aggregate([r for r in rows if r['kind'] == kind])
    (a.output / 'summary.json').write_text(json.dumps({
        'evaluation': 'deterministic student, nominal HOI wrist/object reference, open-hand start; no training DR',
        'checkpoint': str(a.checkpoint.resolve()), 'teacher_model':str(a.teacher_model) if a.teacher_model else None, 'settings': str(a.settings.resolve()),
        'reference_count': len(paths), 'cluster_counts': dict(Counter(labels)),
        'form_steps': a.form_steps, 'hold_extra_steps': a.hold_extra_steps,
        'release_steps': a.release_steps, 'seed': a.seed,
        'metrics_note': '3cm/30deg are object-reference tracking thresholds, not general grasp success; tail_hold_pose_success requires >=80% tail frames inside both thresholds and >=50% tail frames with two object-contacting fingers.',
        'summary': summary,
    }, indent=2) + '\n')
    (a.output / 'episodes.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    (a.output / 'complete.json').write_text(json.dumps({'complete': True, 'episodes': len(rows), 'steps': max_steps}, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)
    wrapped.close()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    if env is not None:
        env.close()
    app.app.close()
