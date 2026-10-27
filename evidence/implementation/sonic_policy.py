"""Robot encoder / bounded continuous-or-FSQ latent / control and motion decoders."""
import torch
from pathlib import Path
from torch import nn
from rsl_rl.modules import ActorCritic
from rsl_rl.runners import OnPolicyRunner
from rsl_rl.networks.normalization import EmpiricalNormalization
from .sonic_distributed import update_normalization
from .sonic_reference import REF_DIM,unpack_reference,masked_reconstruction,GROUPS,rotation_matrix_from_6d,SCHEMA_VERSION


def mlp(input_width,hidden,output_width):
    layers=[]
    for width in hidden:layers.extend((nn.Linear(input_width,width),nn.ELU()));input_width=width
    return nn.Sequential(*layers,nn.Linear(input_width,output_width))


class SonicActor(nn.Module):
    def __init__(self,state_width,actions,options):
        super().__init__();self.state_width=state_width;self.frames=options.get('future_frames',6)
        self.mode=options.get('bottleneck','continuous');self.latent_dim=options.get('latent_dim',32)
        self.encoder=mlp(self.frames*(2*REF_DIM+1),[512,256,128],self.latent_dim)
        self.control=mlp(state_width+self.latent_dim,[512,512,256,128],actions)
        self.motion=mlp(self.latent_dim,[256,256,128],self.frames*REF_DIM)
        self.register_buffer('reference_mean',torch.tensor(options.get('reference_mean',[0.]*REF_DIM)))
        self.register_buffer('reference_std',torch.tensor(options.get('reference_std',[1.]*REF_DIM)))
        levels=options.get('levels',[5]*self.latent_dim)
        if len(levels)!=self.latent_dim or any(x!=5 for x in levels):raise ValueError('V1 supports exactly five scalar levels per latent dimension')
        if self.mode not in ['continuous','fsq']:raise ValueError('Use continuous or fsq')
        self.quantizer=None
        if self.mode=='fsq':
            from vector_quantize_pytorch import FSQ
            # No indices / implicit codebook. 5**32 must never be materialized.
            self.quantizer=FSQ(levels=levels,return_indices=False)
        self.last_reference=None
        self.last_latent=None
        self.freeze_latent=False;self.fixed_latent=None

    def encode(self,packed):
        features,mask,valid=unpack_reference(packed,self.frames)
        target=(features-self.reference_mean)/self.reference_std.clamp_min(.05)
        active=mask&valid[...,None]
        target=torch.where(active,target,0.)
        encoded=torch.cat((target.flatten(1),active.to(target.dtype).flatten(1),valid.to(target.dtype)),-1)
        raw=self.encoder(encoded)
        # Same bounded latent for continuous and FSQ; FSQ library applies tanh internally.
        bounded=torch.tanh(raw)*1.001
        if self.quantizer is None:z=bounded
        else:z=self.quantizer(raw[:,None,:])[0][:,0]
        self.last_latent=(bounded,z)
        self.last_reference=(target,mask,valid)
        return z,target,mask,valid

    def forward(self,observation):
        z,_,_,_=self.encode(observation[...,self.state_width:])
        if self.freeze_latent:
            if self.fixed_latent is None:self.fixed_latent=z.detach().clone()
            z=self.fixed_latent
        return self.control(torch.cat((observation[...,:self.state_width],z),-1))

    def reconstruction(self,observation,reuse_actor_forward=False):
        if reuse_actor_forward:
            if self.last_reference is None or self.last_latent is None or not self.last_latent[1].requires_grad:
                raise RuntimeError('Reconstruction reuse requires the current training actor forward')
            z=self.last_latent[1];target,mask,valid=self.last_reference
        else:z,target,mask,valid=self.encode(observation[...,self.state_width:])
        reconstructed=self.motion(z).reshape(-1,self.frames,REF_DIM)
        loss,groups,missing=masked_reconstruction(reconstructed,target,mask,valid)
        bounded,_=self.last_latent
        # Per-dimension histogram, usage, saturation and entropy; avoid combined token IDs.
        bins=((z.detach()+1)*2).round().long().clamp(0,4)
        histogram=torch.nn.functional.one_hot(bins,5).float().mean(0)
        entropy=-(histogram*histogram.clamp_min(1e-8).log()).sum(-1)
        metrics={'reconstruction':loss,'quantization_mse':(bounded-z).square().mean(),
                 'latent_saturation':(bounded.abs()>.95).float().mean(),'bin_usage_mean':(histogram>0).float().mean(),
                 'bin_entropy_mean':entropy.mean()}
        usage=(histogram>0).float().mean(-1)
        saturation=(bounded.detach().abs()>.95).float().mean(0)
        for i in range(self.latent_dim):
            metrics[f'latent_dim_{i}_usage']=usage[i]
            metrics[f'latent_dim_{i}_entropy']=entropy[i]
            metrics[f'latent_dim_{i}_saturation']=saturation[i]
        for name,value in groups.items():metrics['reconstruction_'+name]=value;metrics['missing_'+name]=missing[name]
        for name in ['object_rotation','wrist_rotation']:
            sl=GROUPS[name];decoded=reconstructed[...,sl]*self.reference_std[sl]+self.reference_mean[sl]
            desired=target[...,sl]*self.reference_std[sl]+self.reference_mean[sl]
            r=rotation_matrix_from_6d(decoded);t=rotation_matrix_from_6d(desired)
            cosine=((r*t).sum((-2,-1))-1)/2;angle=cosine.clamp(-1+1e-6,1-1e-6).acos()
            active=valid&mask[...,sl].all(-1)
            metrics[name+'_so3_error_rad']=(angle*active).sum()/active.sum().clamp_min(1)
        return loss,metrics


class SonicStateNormalizer(nn.Module):
    def __init__(self,width,history_length=8,preserve_masks=False,frame_width=113):
        super().__init__();self.width=width;self.stats=EmpiricalNormalization(width)
        indices=[i*frame_width+j for i in range(history_length) for j in range(frame_width-5,frame_width)]+[frame_width*history_length+15] if preserve_masks else []
        self.register_buffer('mask_indices',torch.tensor(indices,dtype=torch.long))
    def forward(self,x):
        y=self.stats(x[...,:self.width])
        if self.mask_indices.numel():y[...,self.mask_indices]=x[...,self.mask_indices]
        return torch.cat((y,x[...,self.width:]),-1)
    def update(self,x):update_normalization(self.stats,x[...,:self.width])


class SonicActorCritic(ActorCritic):
    def __init__(self,obs,obs_groups,num_actions,sonic,**kwargs):
        kwargs.pop('release_normalization',None);kwargs.update(actor_obs_normalization=False,critic_obs_normalization=False)
        super().__init__(obs,obs_groups,num_actions,**kwargs)
        if num_actions!=22:raise ValueError('SONIC V1 uses 22 finger actions')
        frames=sonic.get('future_frames',6);ref_width=frames*(2*REF_DIM+1)
        aw=sum(obs[k].shape[-1] for k in obs_groups['policy']);cw=sum(obs[k].shape[-1] for k in obs_groups['critic'])
        self.actor=SonicActor(aw-ref_width,num_actions,sonic)
        self.critic=mlp(cw,[512,512,256,128],1)
        self.actor_obs_normalization=True;self.critic_obs_normalization=True
        self.actor_obs_normalizer=SonicStateNormalizer(aw-ref_width,sonic.get('history_length',8),True,111 if sonic.get('no_wrist_xy',False) else 113)
        self.critic_obs_normalizer=SonicStateNormalizer(cw-ref_width)
        self.release_value_normalizer=EmpiricalNormalization(1);self.release_normalized_value=False
        self.reconstruction_weight=sonic.get('reconstruction_weight',.1)
    def update_normalization(self,obs):
        # RSL calls this during collection. Keep behavior normalizers fixed until update ends.
        pass
    def finish_normalization(self,obs):
        self.actor_obs_normalizer.update(self.get_actor_obs(obs))
        self.critic_obs_normalizer.update(self.get_critic_obs(obs))
    def evaluate(self,obs,**kwargs):
        value=super().evaluate(obs,**kwargs)
        return value if self.release_normalized_value else self.release_value_normalizer.inverse(value)
    def actor_parameters(self):
        yield from self.actor.parameters()
        yield self.std if self.noise_std_type=='scalar' else self.log_std


class SonicOnPolicyRunner(OnPolicyRunner):
    def learn(self, num_learning_iterations, init_at_random_ep_len=False):
        print(f'[SONIC startup] rank={getattr(self,"gpu_global_rank",0)} preparing writer',flush=True)
        self._prepare_logging_writer()
        print(f'[SONIC startup] rank={getattr(self,"gpu_global_rank",0)} writer ready',flush=True)
        return super().learn(num_learning_iterations,init_at_random_ep_len)

    def _construct_algorithm(self,obs):
        # Isaac runtime may enable reduced-precision GEMM globally; batch-size changes
        # must not perturb PPO behavior likelihoods before an update.
        torch.set_float32_matmul_precision('highest')
        print('[SONIC] matmul precision:',torch.get_float32_matmul_precision(),'TF32:',torch.backends.cuda.matmul.allow_tf32,flush=True)
        from .sonic_ppo import SonicPPO
        policy=dict(self.policy_cfg);policy.pop('class_name',None)
        algorithm=dict(self.alg_cfg);algorithm.pop('class_name',None)
        model=SonicActorCritic(obs,self.cfg['obs_groups'],self.env.num_actions,**policy).to(self.device)
        alg=SonicPPO(model,device=self.device,multi_gpu_cfg=self.multi_gpu_cfg,**algorithm)
        alg.init_storage('rl',self.env.num_envs,self.num_steps_per_env,obs,[self.env.num_actions])
        return alg
    def save(self,path,infos=None):
        temporary=str(Path(path).with_suffix('.pending.pt'))
        super().save(temporary,infos)
        data=torch.load(temporary,map_location=self.device,weights_only=False)
        data['critic_optimizer_state_dict']=self.alg.critic_optimizer.state_dict()
        data['sonic_schema']=SCHEMA_VERSION;data['sonic_config']=self.policy_cfg['sonic']
        data['sonic_completed_updates']=self.current_learning_iteration+1
        torch.save(data,temporary)
        Path(temporary).replace(path)
    def load(self,path,load_optimizer=True,map_location=None):
        data=torch.load(path,map_location=map_location or self.device,weights_only=False)
        if data.get('sonic_schema')!=SCHEMA_VERSION:raise ValueError('Not a SONIC robot V1 checkpoint')
        if data['sonic_config']!=self.policy_cfg['sonic']:raise ValueError('SONIC configuration differs; use an explicit diagnostic conversion')
        result=super().load(path,load_optimizer,map_location)
        self.current_learning_iteration=data['iter']+1
        if load_optimizer:
            self.alg.critic_optimizer.load_state_dict(data['critic_optimizer_state_dict'])
            self.alg.learning_rate=self.alg.optimizer.param_groups[0]['lr']
        return result
