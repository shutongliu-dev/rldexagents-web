"""Keep method overviews visible while making full technical detail optional."""
import re


SECTIONS = {
    '3-learning-executable-dexterous-skills': {
        'overview': 'A SONIC-style teacher adapts Dex-X training to hand-only control. The policy controls the fingers while an external controller supplies wrist motion; successful interactions support command-conditioned distillation.',
        'label': 'Read training details',
        'description': 'SONIC-style teacher, hand-only training and wrist execution',
    },
    '4-interface-conditioned-skill-distillation': {
        'overview': 'The final student combines Cluster + phase commands with local sensor feedback. Mixed DAgger/PPO training uses teacher action labels on student rollouts together with physical task rewards.',
        'label': 'Read distillation details',
        'description': 'Cluster + phase conditioning and mixed DAgger/PPO training',
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
