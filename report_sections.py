"""Keep method overviews visible while making full technical detail optional."""
import re


SECTIONS = {
    '3-learning-executable-dexterous-skills': {
        'overview': 'Reference-conditioned RL teachers turn retargeted motion into physically executed interactions. Successful lift-and-hold rollouts provide demonstrations for the command-conditioned students.',
        'label': 'Read training details',
        'description': 'Teacher setup, successful-rollout selection and limitations',
    },
    '4-interface-conditioned-skill-distillation': {
        'overview': 'Cluster, Joint, Fingertip and Hybrid commands condition four students with the same control architecture. Students learn from teacher actions on their own rollouts, combined with task PPO in the matched interface study.',
        'label': 'Read distillation details',
        'description': 'Feedback inputs, command formats and teacher–student training',
    },
}


def fold_method_sections(page):
    for section_id, copy in SECTIONS.items():
        pattern = rf'(<h2\b[^>]*id="{section_id}"[^>]*>.*?</h2>)(.*?)(?=<h2\b|</article>)'

        def wrap(match):
            heading, body = match.groups()
            if 'class="method-details"' in body:
                return match.group(0)
            return (
                heading + f'<p class="method-overview">{copy["overview"]}</p>'
                '<details class="method-details">'
                '<summary><span class="method-summary-copy">'
                f'<span class="method-summary-title">{copy["label"]}</span>'
                f'<span class="method-summary-description">{copy["description"]}</span>'
                '</span></summary><div class="method-detail-body">'
                + body + '</div></details>\n'
            )
        page, count = re.subn(pattern, wrap, page, count=1, flags=re.S)
        if count != 1:
            raise ValueError(f'Missing method section: {section_id}')
    return page
