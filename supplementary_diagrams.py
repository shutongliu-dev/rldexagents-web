"""Render supplementary diagrams using the report's paper, serif and teal style."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parent
FIG = ROOT / 'figures'
INK = '#27241f'
MUTED = '#81735f'
TEAL = '#36766d'
RULE = '#d8d0c2'
ARROW = '#a49b8b'
TITLE = FontProperties(fname=ROOT / 'assets/fonts/dexx-template-1.ttf')
BODY = FontProperties(fname=ROOT / 'assets/fonts/dexx-template-3.ttf')


def canvas(height):
    fig = plt.figure(figsize=(12, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 12), ylim=(0, height))
    ax.axis('off')
    return fig, ax


def text(ax, x, y, value, size=10, color=INK, title=False, align='center'):
    return ax.text(x, y, value, ha=align, va='center', fontsize=size,
                   color=color, fontproperties=TITLE if title else BODY,
                   linespacing=1.7)


def arrow(ax, start, end):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle='->',
                                mutation_scale=11, lw=.9, color=ARROW))


def rule(ax, y):
    ax.plot([.25, 11.75], [y, y], color=RULE, lw=.75)


def node(ax, x, y, label, title, body, accent=False):
    text(ax, x, y+.48, label, 8, MUTED)
    text(ax, x, y+.12, title, 15, TEAL if accent else INK, title=True)
    text(ax, x, y-.38, body, 9, MUTED)


def save(fig, name):
    with plt.rc_context({'svg.fonttype': 'path', 'pdf.fonttype': 42}):
        for extension in ('svg', 'png', 'pdf'):
            path = FIG / f'{name}.{extension}'
            fig.savefig(path, dpi=180, bbox_inches='tight', pad_inches=.14,
                        transparent=True)
            if extension == 'svg':
                path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    plt.close(fig)


def draw_overview():
    fig, ax = canvas(4.8)
    text(ax, .3, 4.57, 'REPRESENTATION & PHYSICAL LEARNING', 8, MUTED, align='left')
    top = [('01', 'Motion data', 'Human & robot motion\nHOI references'),
           ('02', 'Pose analysis', 'PCA & interaction geometry\nRepresentative configurations'),
           ('03', 'Pose bank', 'Quasi-static references\nRetrieval & reuse'),
           ('04', 'RL teacher', 'SONIC-style hand control\nExternal wrist reference')]
    for x, item in zip((1.5, 4.5, 7.5, 10.5), top):
        node(ax, x, 3.52, *item)
    for x in (1.5, 4.5, 7.5):
        arrow(ax, (x+1.08, 3.65), (x+1.86, 3.65))
    rule(ax, 2.55)
    text(ax, .3, 2.3, 'DISTILLATION & AGENT EXECUTION', 8, MUTED, align='left')
    bottom = [('07', 'Agent execution', 'Cluster + phase commands\nHand feedback & arm motion'),
              ('06', 'Skill bank', 'Trained feedback policies\nRuntime & outcome information'),
              ('05', 'Distillation', 'Mixed DAgger / PPO\nStudent-visited state labels')]
    for x, item in zip((2, 6, 10), bottom):
        node(ax, x, 1.15, *item, accent=True)
    arrow(ax, (10.5, 2.93), (10.1, 1.84))
    arrow(ax, (8.55, 1.28), (7.45, 1.28))
    arrow(ax, (4.55, 1.28), (3.45, 1.28))
    save(fig, 'fig01_overview')


def draw_distillation():
    fig, ax = canvas(4.9)
    text(ax, .3, 4.67, 'TRAINING', 8, MUTED, align='left')
    for x, item in zip((2, 6, 10), [
        ('01', 'Reference teacher', 'Object state & future motion\nSONIC-style hand policy'),
        ('02', 'Online action labels', 'Teacher supervision at\nstudent-visited states'),
        ('03', 'Mixed DAgger / PPO', 'Action imitation & task reward\nPrivileged training critic')]):
        node(ax, x, 3.62, *item)
    arrow(ax, (3.35, 3.75), (4.5, 3.75))
    arrow(ax, (7.5, 3.75), (8.5, 3.75))
    rule(ax, 2.66)
    text(ax, .3, 2.4, 'FINAL STUDENT', 8, MUTED, align='left')
    for x, item in zip((2, 6, 10), [
        ('INPUT', 'Local feedback', 'Proprioception & tactile history\nPrevious actions'),
        ('COMMAND', 'Cluster + phase', 'Grasp family & execution stage\nRecurrent hand controller'),
        ('OUTPUT', 'Finger control', 'Decode & smooth targets\nApply physical joint limits')]):
        node(ax, x, 1.27, *item, accent=True)
    arrow(ax, (3.4, 1.4), (4.5, 1.4))
    arrow(ax, (7.5, 1.4), (8.6, 1.4))
    text(ax, 6, .22, 'The student executes the rollout; the teacher labels its visited states.', 8.5, MUTED)
    save(fig, 'fig03_distillation')


def draw_interfaces():
    fig, ax = canvas(3.9)
    text(ax, .3, 3.67, 'INTERFACE ABLATION', 8, MUTED, align='left')
    for x, item in zip((1.5, 4.5, 7.5, 10.5), [
        ('A', 'Cluster', 'Configuration family\nDiscrete grasp intent'),
        ('B', 'Joint', 'Target hand pose\nJoint-space geometry'),
        ('C', 'Fingertip', 'Palm-frame targets\nEndpoint geometry'),
        ('D', 'Hybrid', 'Cluster & fingertips\nDiscrete + geometric intent')]):
        node(ax, x, 2.65, *item, accent=True)
        ax.plot([x, x], [1.9, 1.6], lw=.8, color=RULE)
    ax.plot([1.5, 10.5], [1.6, 1.6], lw=.8, color=RULE)
    arrow(ax, (6, 1.6), (6, 1.27))
    text(ax, 6, 1, 'Shared feedback & control architecture', 16, title=True)
    text(ax, 6, .5, 'Hand feedback + command + phase  /  recurrent policy  /  finger actions', 9, MUTED)
    save(fig, 'fig04_interfaces')


def draw_runtime():
    fig, ax = canvas(4.9)
    text(ax, .35, 4.66, 'AGENT & HAND RUNTIME', 8, MUTED, align='left')
    for y, item in zip((3.62, 2.2, .78), [
        ('01', 'Agent command', 'Select cluster & phase\nCoordinate external wrist motion'),
        ('02', 'Hand controller', 'Sensor history & policy inference\nSmoothed finger targets'),
        ('03', 'Execution feedback', 'Contact status\nObject-level outcome verification')]):
        node(ax, 3, y, *item, accent=True)
    arrow(ax, (3, 3.02), (3, 2.86))
    arrow(ax, (3, 1.6), (3, 1.44))
    ax.plot([6, 6], [.25, 4.3], color=RULE, lw=.75)
    photo = fig.add_axes([.55, .18, .42, .67])
    photo.imshow(plt.imread(FIG / 'physical_readonly_rgb.png'))
    photo.axis('off')
    text(ax, 9.12, 4.48, 'Physical camera observation', 14, title=True)
    text(ax, 9.12, .43, 'Read-only capture · no motion sent', 8.5, MUTED)
    save(fig, 'fig07_runtime')


if __name__ == '__main__':
    draw_overview()
    draw_distillation()
    draw_interfaces()
    draw_runtime()
