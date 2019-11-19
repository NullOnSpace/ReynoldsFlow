from django.utils import timezone

from .models import Flow, Node
from .flows import FLOWS

import importlib


def get_task_dict(user):
    unassigned = Flow.objects.filter(status=0, head_node__owner=None)
    unaccepted = Node.objects.filter(status=0, owner=user)
    handling = Node.objects.filter(status=1, owner=user)
    handled = Flow.objects.filter(
        status__gt=1, node__owner=user).distinct().exclude(
        node__status__in=[0, 1], node__owner=user)
    finish = Flow.objects.filter(status=2, head_node__owner=user)
    frozen = Flow.objects.filter(status=3, head_node__owner=user)
    data = {
        'unassigned': unassigned, 'unaccepted': unaccepted,
        'handling': handling, 'handled': handled,
        'finish': finish, 'frozen': frozen,
    }
    return data


def get_node_destination(node):
    return FLOWS[node.flow.flow_name]["flow"][node.name]['destination']


def get_node_flow(node):
    return FLOWS[node.flow.flow_name]["flow"]


def get_node_entry(node):
    entry = FLOWS[node.flow.flow_name]["flow"][node.name].get("entry")
    if entry:
        module_path, fn_name = entry.rsplit(".", maxsplit=1)
        mod = importlib.import_module(module_path)
        fn = getattr(mod, fn_name)
        if callable(fn):
            return fn
    return None


def check_action_in_node(node, action, user, phase=None):
    """
    Check if the specified action on the node by the user is valid.
    First check if the action can be act on the node in current status.
    Then check if the phase aka the name of the the next node is valid
    after action acted on current node.
    Return True and Permission codename if check pass,
    otherwise return False and the reason it doesn't pass.
    It doesn't check if the use has permission to act on the node,
    which can be done outside this function by check the user is the owner of
    the node.
    """
    destination = get_node_destination(node)
    flow = get_node_flow(node)
    # a dict mapping node's status to the actions
    # that can be done in the corresponding status.
    status_dict = {
        0: {'accept', 'delegate'}, 1: {'default', 'spe_commit', 'refuse'},
    }
    valid_actions = status_dict.get(node.status, set())
    if action not in valid_actions:
        return False, "node not in status"
    else:
        flow = get_node_flow(node)
        destination = get_node_destination(node)
        if phase is not None:
            # phase is the specified node name of next action
            if action == "delegate":
                if phase != node.name:
                    return False, "delegate to different phase"
            else:
                # when commit, spe_commit and refuse
                valid_phases = destination[action]
                if phase not in valid_phases and phase != valid_phases:
                    return False, "phase not right"
            permission = flow[phase]["permission"]
        else:
            if action == "default":
                if destination['default'] is not None:
                    return False, "try to commit to end but not over yet"
            elif action == "spe_commit":
                if None not in destination['spe_commit']:
                    return False, "try to spe commit to end but not over yet"
            elif action not in ['accept', 'delegate']:
                return False, "action requires a phase but None"
            # this happens when commit or spe_commit to end
            permission = None
        return True, permission


def handle_node_action(node, action, phase=None, to_user=None):
    """
    Return the node that should be working on after the action being acted,
    which can be either a new node or the original node with a new status.
    And return the flow if after the action the flow goes to an end.
    """
    if action == "accept":
        node.status = 1
        node.accept = timezone.now()
        node.save()
        return node
    else:
        # the node will go to end after all actions other than accept
        node.end = timezone.now()
        flow = node.flow
        status_mapping = {
            'default': 2, 'delegate': 3, 'refuse': 4, 'spe_commit': 5,
        }
        node.status = status_mapping[action]
        if phase:
            # create new node
            next_node = Node.objects.create(
                name=phase, owner=to_user, flow=node.flow, order=node.order+1
            )
            node.next_node = next_node
            node.save()
            return next_node
        else:
            node.save()
            # this flow is end
            flow.status = 2
            flow.save()
            return flow


# def get_node_view(node):
#     flow = get_node_flow(node)
#     view_fn = flow[node.name].get("view", None)
#     if view_fn:
#         view = importlib.import_module(view_fn)
#         if callable(view):
#             return view
#     return None
