from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name, HtmlLexer, PythonLexer


from django import template
from django.core.urlresolvers import reverse_lazy
from django.template import Node
from django.utils.safestring import mark_safe

register = template.Library()


# usage: {% pygmentize "language" %}...language text...{% endpygmentize %}
class PygmentizeNode(Node):
    def __init__(self, nodelist, language):
        self.nodelist, self.language = nodelist, language

    def render(self, context):
        try:
            lexer = get_lexer_by_name(self.language)
        except:
            lexer = HtmlLexer()
        return highlight(self.nodelist.render(context), lexer, HtmlFormatter())


@register.tag(name='pygmentize')
def pygmentize(parser, token):
    tag_name, format_string = token.split_contents()
    nodelist = parser.parse(('endpygmentize',))
    parser.delete_first_token()
    return PygmentizeNode(nodelist, format_string[1:-1])


@register.simple_tag
def active(path, url):
    if path == reverse_lazy(url):
        return 'active'
    else:
        return ''


# usage: {{ text|pygmentize:'language' }}
@register.filter
def pygmentize(text, language):
    """Pygmentizes the given block of text."""
    try:
        lexer = get_lexer_by_name(language)
    except:
        lexer = HtmlLexer()
    return mark_safe(highlight(text, lexer, HtmlFormatter()))
