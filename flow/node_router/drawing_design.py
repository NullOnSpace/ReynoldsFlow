# from ..models import Flow, Node
from django.shortcuts import render

from drawing.forms import DrawingForm


def design(request, node, user, dest):
    if request.method == "GET":
        drawings = node.flow.drawings.order_by('create')
        form = DrawingForm()
        context = {
            'drawings': drawings, 'node': node, 'allow_commit': True,
            'dest': dest, 'form': form,
        }
        return render(request, 'drawing/drawing_design/design.html', context)
