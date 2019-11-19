# from ..models import Flow, Node
from django.shortcuts import render


def design(request, node, user, dest):
    if request.method == "GET":
        drawings = node.flow.drawings.order_by('create')
        context = {
            'drawings': drawings, 'node': node, 'allow_commit': True,
            'dest': dest
        }
        return render(request, 'drawing/drawing_design/design.html', context)
