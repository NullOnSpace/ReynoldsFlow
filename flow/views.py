from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.decorators import login_required
from django.forms.models import modelform_factory
from django.forms import widgets
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.template import loader

from .flows import FLOWS
from .models import Flow, Node, User
from .utils import (get_task_dict, check_action_in_node, get_node_destination,
                    handle_node_action,)


# Create your views here.
@login_required
def index(request):
    return render(request, 'flow/index.html', {
        'section': 'home',
    })


@login_required
def create_flow(request):
    user = request.user
    flow_names = list(FLOWS.keys())
    flow_choices = list(zip(flow_names, flow_names))
    FlowForm = modelform_factory(model=Flow,
                                 fields=('name', 'flow_name', 'desc'),
                                 widgets={
                                     'flow_name':
                                         widgets.Select(choices=flow_choices)
                                 })
    if request.method == "POST":
        form = FlowForm(request.POST)
        if form.is_valid():
            flow = form.save(commit=False)
            flow.sponsor = user
            flow.save()
            return redirect('init_flow', flow.id)
    else:
        form = FlowForm()
    return render(request, 'flow/create_flow.html', {
        'form': form, 'section': 'create_flow',
    })


@login_required
def initialize_flow(request, flow_id):
    flow = get_object_or_404(Flow, pk=flow_id)
    user = request.user
    try:
        phase = FLOWS[flow.flow_name]['start']
    except KeyError:
        return render(request, 'flow/index.html', {
                'section': 'home', 'msg': {
                    'level': 'warning',
                    'content': 'flow %s not configured correctly'
                               % (flow.flow_name,)
                }
            })
    if flow.sponsor != user:
        return render(request, 'flow/index.html', {
                'section': 'home', 'msg': {
                    'level': 'warning',
                    'content': 'Not the sponsor is assigning',
                }
            })
    if flow.head_node:
        return render(request, 'flow/index.html', {
                'section': 'home', 'msg': {
                    'level': 'warning',
                    'content': 'Flow has been assigned!'.format(flow)
                }
            })
    users = User.objects.values_list('id', 'username')
    user_ids = list(zip(*users))[0]
    NodeForm = modelform_factory(Node, fields=('owner',), widgets={
        'owner': widgets.Select(choices=users)
    })
    if request.method == "POST":
        form = NodeForm(request.POST)
        if form.is_valid():
            node = form.save(commit=False)
            node.flow = flow
            node.name = phase
            node.order = 0
            node.save()
            flow.status = 1
            flow.head_node = node
            flow.save()
            if node.owner == user:
                return redirect('show_node', node.pk)
            else:
                return render(request, 'flow/index.html', {
                    'section': 'home', 'msg': {
                        'level': 'success',
                        'content': 'Assign: {} successfully!'.format(flow)
                    }
                })
    else:
        if user.pk in user_ids:
            form = NodeForm(initial={'owner': user.pk})
        else:
            form = NodeForm()
    return render(request, 'flow/initialize_flow.html', {
        'form': form, 'flow': flow, 'phase': phase, 'section': 'create_flow',
    })


@login_required
def show_node(request, node_id):
    node = get_object_or_404(Node, pk=node_id)
    dest = get_node_destination(node)
    return render(request, 'flow/show_node.html', {
        'node': node, 'section': 'task', 'dest': dest, 'allow_commit': True,
    })


@login_required
def show_flow(request, flow_id):
    flow = get_object_or_404(Flow, pk=flow_id)
    return render(request, 'flow/show_flow.html', {
        'section': 'home', 'flow': flow,
    })


def ajax_get_task_stat(request):
    ret = {'code': 'fail'}
    user = request.user
    if not user.is_authenticated:
        ret['msg'] = 'user not login'
        return JsonResponse(ret)
    qs_dict = get_task_dict(user)
    data = dict()
    for cate, qs in qs_dict.items():
        data[cate] = qs.count()
    ret['code'] = 'success'
    ret['data'] = data
    return JsonResponse(ret)


def ajax_get_task_list(request):
    ret = {'code': 'fail'}
    user = request.user
    if not user.is_authenticated:
        ret['msg'] = 'user not login'
        return JsonResponse(ret)
    task_cate = request.GET.get("cate")
    qs_dict = get_task_dict(user)
    task_qs = qs_dict.get(task_cate, None)
    if task_qs is not None:
        tasks = task_qs.order_by('-create')
        data = list()
        for task in tasks:
            data.append((task.get_absolute_url(), str(task)))
        ret['code'] = 'success'
        ret['data'] = data
        return JsonResponse(ret)
    else:
        ret['msg'] = "incorrect cate name"
        return JsonResponse(ret)


def ajax_check_node_action(request):
    ret = {'code': 'fail'}
    user = request.user
    method = request.method
    query_dict = getattr(request, method)
    if not user.is_authenticated:
        ret['msg'] = 'user not login'
        return JsonResponse(ret)
    node_pk = query_dict.get('node')
    try:
        node = Node.objects.get(pk=node_pk)
    except Node.DoesNotExist:
        ret['msg'] = "node does not exist"
        return JsonResponse(ret)
    if node.owner != user:
        ret['msg'] = "no permission to edit node"
        return JsonResponse(ret)
    action = query_dict.get('action', None)
    phase = query_dict.get('phase', None)
    checked, extra = check_action_in_node(node, action, user, phase)
    if checked:
        ret['code'] = "success"
        if phase is not None:
            permission = extra
            if method == "POST":
                to_pk = request.POST.get('to')
                try:
                    to_user = User.objects.get(pk=to_pk)
                except User.DoesNotExist:
                    ret['code'] = 'fail'
                    ret['msg'] = "to user not exist"
                    return JsonResponse(ret)
                # check if to_user has perm
                if (not to_user.has_perm(permission) or
                        (action == "delegate" and node.owner == to_user)):
                    ret['code'] = "fail"
                    ret['msg'] = "to-user not valid"
                    return JsonResponse(ret)
                # if to_user checked create new node or change node status
                new_node = handle_node_action(node, action, phase, to_user)
                # just for debug
                assert isinstance(new_node, Node)
                if new_node.owner == user:
                    href = reverse("show_node", args=(new_node.pk,))
                else:
                    # should be the flow page
                    href = reverse("index")
                ret["href"] = href
            else:
                print(permission)
                perm = Permission.objects.get(codename=permission)
                groups = perm.group_set.all()
                user_qs = None
                print(groups)
                for group in groups:
                    qs = group.user_set.all()
                    if user_qs is None:
                        user_qs = qs
                    else:
                        user_qs.union(qs)
                print(user_qs)
                # in case that grant a user for special permission
                user_qs.union(perm.user_set.all())
                users =  [
                    (pk, username)
                    for pk, username in user_qs.values_list('pk', 'username')
                    if not (action=="delegate" and pk==node.owner.pk)
                ]
                ret['users'] = users
        else:
            if method == "POST":
                # accept or the end
                # to determine what's next href
                obj = handle_node_action(node, action)
                if isinstance(obj, Node):
                    # accept situation
                    href = reverse("show_node", args=(obj.pk,))
                else:
                    # end, should be the flow page
                    href = reverse("show_flow", args=(node.flow.pk,))
                ret["href"] = href
        return JsonResponse(ret)
    else:
        # extra is error msg
        ret['msg'] = extra
        return JsonResponse(ret)


def ajax_get_node_detail(request):
    pk = request.GET.get('pk')
    node = Node.objects.get(pk=pk)
    tpl = loader.get_template('flow/node_detail_frag.html')
    context = {'node': node}
    return HttpResponse(tpl.render(context, request))
