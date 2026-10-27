"""Mixed DAgger/PPO learner for the deployable 8x117 cluster command actor."""

import copy

import torch
from torch import nn
from torch.distributions import Normal, TransformedDistribution
from torch.distributions.transforms import TanhTransform

from .c0_command_student import C0CommandStudent
from .grasp_rl import generalized_advantage


class ClusterMixedPPO:
    """Train C0-style local hand actor with online DAgger and task PPO losses."""

    def __init__(self, saved, critic_width, device, actor_lr=3e-6,
                 critic_lr=3e-4, initial_std=.08):
        self.saved = copy.deepcopy(saved)
        self.device = torch.device(device)
        count = int(saved["metadata"].get("num_grasps", 6))
        if count != 6:
            raise ValueError("Link-near student requires six cluster command channels")
        if saved['metadata'].get('interface'):
            from .interface_student import InterfaceStudent
            with torch.random.fork_rng(devices=[]):
                self.student = InterfaceStudent(saved['metadata']['interface']).to(device)
        else:
            self.student = C0CommandStudent(count).to(device)
        self.student.load_state_dict(saved["student_state_dict"])
        self.action_scale = torch.as_tensor(saved["action_scale"], device=device).float()
        self.action_offset = torch.as_tensor(saved["action_offset"], device=device).float()
        self.critic = nn.Sequential(nn.LayerNorm(critic_width), nn.Linear(critic_width, 256),
                                    nn.ELU(), nn.Linear(256, 128), nn.ELU(),
                                    nn.Linear(128, 1)).to(device)
        self.log_std = nn.Parameter(torch.full((22,), float(torch.tensor(initial_std).log()),
                                               device=device))
        self.optimizer = torch.optim.Adam([
            {"params": self.student.parameters(), "lr": actor_lr},
            {"params": [self.log_std], "lr": actor_lr},
            {"params": self.critic.parameters(), "lr": critic_lr},
        ])
        self.updates = 0

    def distribution(self, history):
        actor_output = self.student(history).clamp(-.999, .999)
        base_location = torch.atanh(actor_output)
        std = self.log_std.clamp(-5., -1.).exp().expand_as(base_location)
        return TransformedDistribution(Normal(base_location, std),
                                       [TanhTransform(cache_size=1)])

    @torch.no_grad()
    def act(self, history, critic):
        dist = self.distribution(history)
        action = dist.rsample()
        return action, dist.log_prob(action).sum(-1), self.critic(critic).squeeze(-1)

    @torch.no_grad()
    def value(self, critic):
        return self.critic(critic).squeeze(-1)

    def update(self, batch, lambda_dagger, *, epochs=4, batch_size=512,
               entropy_coef=.002, critic_only=False):
        if not 0. <= lambda_dagger <= 1.:
            raise ValueError("lambda_dagger must be in [0, 1]")
        advantages, returns = generalized_advantage(
            batch["reward"], batch["value"], batch["next_value"],
            batch["terminal"], batch["valid"])
        valid = batch["valid"].bool()
        flat = {key: value.flatten(0, 1)[valid.flatten()]
                for key, value in batch.items()}
        advantages = advantages.flatten()[valid.flatten()]
        returns = returns.flatten()[valid.flatten()]
        if not len(advantages):
            raise ValueError("No active rollout transitions")
        advantages = (advantages - advantages.mean()) / advantages.std(unbiased=False).clamp_min(1e-6)
        rows = []
        sample_visits = 0
        for _ in range(epochs):
            for indices in torch.randperm(len(advantages), device=self.device).split(batch_size):
                dist = self.distribution(flat["history"][indices])
                log_prob = dist.log_prob(flat["action"][indices]).sum(-1)
                log_ratio = log_prob - flat["log_prob"][indices]
                ratio = log_ratio.exp()
                ppo = -torch.minimum(ratio * advantages[indices],
                                     ratio.clamp(.8, 1.2) * advantages[indices]).mean()
                # A tanh-transformed Gaussian has no closed-form entropy; the
                # negative log probability is a stable entropy proxy here.
                ppo += entropy_coef * log_prob.mean()
                dagger = (self.student(flat["history"][indices])
                          - flat["teacher_action"][indices]).square().mean()
                value = .5 * (self.critic(flat["critic"][indices]).squeeze(-1)
                              - returns[indices]).square().mean()
                policy_loss = lambda_dagger * dagger + (1. - lambda_dagger) * ppo
                loss = value if critic_only else policy_loss + value
                if not torch.isfinite(loss):
                    raise RuntimeError("Nonfinite cluster mixed DAgger/PPO loss")
                self.optimizer.zero_grad(set_to_none=True)
                loss.backward()
                nn.utils.clip_grad_norm_(self.student.parameters(), 1.)
                nn.utils.clip_grad_norm_(self.critic.parameters(), 1.)
                nn.utils.clip_grad_norm_([self.log_std], 1.)
                self.optimizer.step()
                approx_kl = ((ratio - 1.) - log_ratio).mean().detach()
                sample_visits += len(indices)
                rows.append(torch.stack((ppo.detach(), dagger.detach(), value.detach(), approx_kl)))
                if approx_kl > .03:
                    break
            if rows[-1][-1] > .03:
                break
        self.updates += 1
        values = torch.stack(rows).mean(0).cpu().tolist()
        metrics = dict(zip(("ppo_policy_loss", "online_dagger_loss", "value_loss", "approx_kl"), values))
        metrics.update(optimizer_steps=len(rows), optimized_sample_visits=sample_visits)
        return metrics

    def save(self, folder, metadata):
        from pathlib import Path
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        saved = {**self.saved,
                 "student_state_dict": {key: value.detach().cpu()
                                        for key, value in self.student.state_dict().items()},
                 "metadata": {**self.saved["metadata"], **metadata,
                              "mixed_ppo_updates": self.updates}}
        torch.save(saved, folder / "student.pt")
        torch.save({"critic": self.critic.state_dict(),
                    "log_std": self.log_std.detach().cpu(),
                    "optimizer": self.optimizer.state_dict(), "updates": self.updates},
                   folder / "rl_state.pt")
