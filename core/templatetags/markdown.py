from django import template
import markdown

register = template.Library()


class MarkdownNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        output = markdown.markdown(
            output, extensions=["toc"], extension_configs={"toc": {"anchorlink": True}}
        )
        return output


@register.tag(name="markdown")
def do_markdown(parser, token):
    nodelist = parser.parse(("endmarkdown",))
    parser.delete_first_token()
    return MarkdownNode(nodelist)
