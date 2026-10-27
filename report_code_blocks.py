"""Local, dependency-free Python highlighting for the report's code examples."""
import html
import io
import keyword
import re
import tokenize


def highlight_python(source):
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def position(point):
        row, column = point
        return offsets[min(row - 1, len(lines))] + column

    tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    parts, cursor = [], 0
    for index, token in enumerate(tokens):
        kind = None
        if token.type == tokenize.STRING:
            kind = 'string'
        elif token.type == tokenize.NUMBER:
            kind = 'number'
        elif token.type == tokenize.COMMENT:
            kind = 'comment'
        elif token.type == tokenize.NAME:
            if keyword.iskeyword(token.string):
                kind = 'keyword'
            elif index + 1 < len(tokens) and tokens[index + 1].string == '(':
                kind = 'function'
        if kind is None:
            continue
        start, end = position(token.start), position(token.end)
        parts.append(html.escape(source[cursor:start]))
        parts.append(f'<span class="tok-{kind}">{html.escape(source[start:end])}</span>')
        cursor = end
    parts.append(html.escape(source[cursor:]))
    return ''.join(parts)


def style_code_blocks(body):
    def render(match):
        source = html.unescape(match.group(1))
        return (
            '<div class="code-example">'
            '<div class="code-toolbar"><span class="code-language">Python</span>'
            '<span class="code-caption">Skill API</span></div>'
            '<pre><code class="language-python">'
            + highlight_python(source)
            + '</code></pre></div>'
        )
    return re.sub(r'<pre><code class="language-python">(.*?)</code></pre>', render, body, flags=re.S)
