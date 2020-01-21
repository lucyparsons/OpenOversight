import pdb as pdb_module

from django.template import Library, Node

register = Library()


class PdbNode(Node):

    def render(self, context):
        pdb_module.set_trace()
        return ''

    @register.tag
    def pdb(parser, token):
        return PdbNode()
