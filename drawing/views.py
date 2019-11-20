from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Max

from flow.models import Node
from .forms import DrawingForm
from .models import DrawingNode, DrawingNodeFlowRel


# Create your views here.
@login_required
def ajax_upload_drawing(request, node_id):
    ret = {'code': 'fail'}
    try:
        node = Node.objects.get(pk=node_id)
    except Node.DoesNotExist:
        ret['msg'] = "node cant find"
        return JsonResponse(ret)
    if request.method == "POST":
        drawing = DrawingForm(request.POST, request.FILES)
        print(request.FILES.get('location'))
        print(request.POST)
        if drawing.is_valid():
            drawing = drawing.save(commit=False)
            id_name = drawing.location.name.split('/')[-1].split('_')[0]
            dn, created = DrawingNode.objects.get_or_create(name=id_name)
            if created:
                dn.author = request.user
                DrawingNodeFlowRel.objects.create(
                    flow=node.flow, drawing_node=dn)
                dn.save()
            drawing.drawing_node = dn
            drawing.author = request.user
            qs = drawing.drawing_node.drawing_set.aggregate(Max('order'))
            drawing.order = (qs['order__max'] or 0) + 1
            drawing.save()
            ret['code'] = 'success'
            return JsonResponse(ret)
        else:
            print(drawing.errors)
            ret['msg'] = "form not validate"
    else:
        ret['msg'] = 'invalid request method'
    return JsonResponse(ret)
