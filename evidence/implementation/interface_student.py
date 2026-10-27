"""Four fixed grasp-command interfaces sharing the existing C GRU backbone."""
import copy
import torch
from torch import nn

PAYLOAD_WIDTH={'cluster':6,'joint':22,'fingertip':15,'hybrid':21}

class InterfaceStudent(nn.Module):
    def __init__(self,interface):
        super().__init__()
        self.interface=interface;self.frame_width=107+PAYLOAD_WIDTH[interface]+4
        self.frame=nn.Sequential(nn.Linear(self.frame_width,192),nn.ELU())
        self.history=nn.GRU(192,192,batch_first=True)
        self.head=nn.Sequential(nn.Linear(192,128),nn.ELU(),nn.Linear(128,22),nn.Tanh())
    def forward(self,history):
        if history.shape[-2:]!=(8,self.frame_width):raise ValueError(f'Expected H8x{self.frame_width}')
        _,h=self.history(self.frame(history));return self.head(h[-1])


def initialize_interface(saved,interface):
    """Copy identical feedback/phase control; zero all new command columns."""
    result=copy.deepcopy(saved)
    with torch.random.fork_rng(devices=[]):
        model=InterfaceStudent(interface)
    weights={k:v.clone() for k,v in saved['student_state_dict'].items()}
    old=weights['frame.0.weight']
    if old.shape!=(192,117):raise ValueError('Initialization must be original C H8x117')
    new=old.new_zeros((192,model.frame_width));new[:,:107]=old[:,:107];new[:,-4:]=old[:,-4:]
    weights['frame.0.weight']=new;model.load_state_dict(weights)
    result['student_state_dict']=weights
    result['metadata'].update(interface=interface,frame_width=model.frame_width,command_units='q radians; fingertips palm meters',
                              fingertip_scale_m=.1,fixed_command=True,num_grasps=6)
    return result


def encode_command(interface,cluster,q_seed,tips,phase,age_s,scale,offset):
    """Raw API units -> network command. Same phase/age suffix in all arms."""
    if phase.shape!=age_s.shape:raise ValueError('phase and age shapes differ')
    if torch.any((phase<0)|(phase>2)):raise ValueError('Invalid phase')
    if not torch.isfinite(age_s).all() or torch.any(age_s<0):raise ValueError('Invalid phase age')
    parts=[]
    if interface in ('cluster','hybrid'):
        if cluster.shape!=phase.shape or torch.any((cluster<0)|(cluster>5)):raise ValueError('Invalid cluster')
        parts.append(torch.nn.functional.one_hot(cluster.long(),6).float())
    if interface=='joint':
        if q_seed.shape!=(*phase.shape,22) or not torch.isfinite(q_seed).all():raise ValueError('Invalid joint command')
        parts.append((q_seed-offset)/scale.clamp_min(1e-6))
    if interface in ('fingertip','hybrid'):
        if tips.shape!=(*phase.shape,5,3) or not torch.isfinite(tips).all():raise ValueError('Invalid fingertip command')
        parts.append(tips.flatten(-2)/.1)
    if interface not in PAYLOAD_WIDTH:raise ValueError('Unknown interface')
    parts.extend([torch.nn.functional.one_hot(phase.long(),3).float(),age_s.clamp(max=5)[...,None]/5])
    return torch.cat(parts,-1)
