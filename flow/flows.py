import warnings
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


FLOWS = {
    'drawing_design': {
        'desc': 'a flow to design new series of project drawings',
        'start': 'design',
        'flow': {
            'design': {
                # 'groups': ['designer'],
                'permission': 'design',
                'entry': 'flow.node_router.drawing_design.design',
                'destination': {
                    'default': 'proof',
                },
            },
            'proof': {
                # 'groups': ['checker'],
                'permission': 'design',
                # 'entry': 'drawing_design_proof',
                'destination': {
                    'default': 'audit',
                    'refuse': ['design'],
                }
            },
            'audit': {
                # 'groups': ['auditor'],
                'permission': 'design',
                # 'entry': 'drawing_design_audit',
                'destination': {
                    'default': 'standard_audit',
                    'refuse': ['design'],
                    'spe_commit': ['final_audit'],
                }
            },
            'standard_audit': {
                # 'groups': ['standard_checker'],
                'permission': 'check',
                # 'entry': 'drawing_design_standard_audit',
                'destination': {
                    'default': 'final_audit',
                    'refuse': ['design'],
                }
            },
            'final_audit': {
                # 'groups': ['boss'],
                'permission': 'check',
                # 'entry': 'drawing_design_final_audit',
                'destination': {
                    'default': None,
                    'refuse': ['design'],
                }
            }
        },
    },
}


def check_permissions(auto_create=False):
    ct = ContentType.objects.get_by_natural_key('flow', 'node')
    for flow_name, flow_def in FLOWS.items():
        for phase_name, phase_def in flow_def['flow'].items():
            permission = phase_def['permission']
            perm_codename = 'flow.'+permission
            if auto_create:
                obj, created = Permission.objects.get_or_create(
                    codename=perm_codename,
                    defaults=dict(name=permission, content_type=ct)
                )
            else:
                created = (not
                    Permission.objects.filter(codename=perm_codename).exists()
                )
            if created:
                info = (
                    f'No such a permission "{permission}" '
                    f'for phase {phase_name} in flow {flow_name} .' +
                    ('Creat a new perm "{}".'.format(perm_codename)
                     if auto_create else '')
                )
                warnings.warn(info)


def check_flows():
    for flow_name, flow_def in FLOWS.items():
        start = flow_def.get('start')
        if start is None:
            raise ValueError(
                'Forget to define a start in flow {}'.format(flow_name))
        flow = flow_def.get('flow')
        if flow is None:
            raise ValueError(
                'Forget to define a flow in flow {}'.format(flow_name))
        phase_names = set(flow.keys())
        if start not in phase_names:
            raise ValueError('start phase: {} not defined '.format(start) +
                             "in flow {}'s phases".format(flow_name))
        for phase_name, phase in flow.items():
            # groups = phase.get('groups')
            # check if group in groups are defined in models
            # entry = phase.get('entry')
            # check if entry name can be reversed into url_pattern
            destination = phase.get('destination')
            if destination is None:
                raise ValueError('no destination defined in'
                                 ' phase {} of '.format(phase_name) +
                                 "flow {}".format(flow_name))
            try:
                default = destination['default']
            except KeyError:
                raise ValueError(
                    'phase {} in flow {} '.format(phase_name, flow_name) +
                    "doesn't have a default in destination"
                )
            if default == phase_name:
                raise ValueError(
                    'phase {} in flow {}'.format(phase_name, flow_name) +
                    ' has a destination to itself in default')
            refuses = destination.get('refuse')
            for refuse in refuses:
                if refuse not in phase_names:
                    warnings.warn('refuse destination: {}'.format(refuse) +
                                  'not in phase {} '.format(phase_name) +
                                  "of flow {}".format(flow_name))
                if refuse == phase_name:
                    raise ValueError(
                        'phase {} in flow {}'.format(phase_name, flow_name)\
                        + ' has a destination to itself in refuse')
            spe_commits = destination.get('spe_commit')
            for spe_commit in spe_commits:
                if spe_commit not in phase_names:
                    warnings.warn(
                        'spe_commit destination: {}'.format(spe_commit) +
                        'not in phase {} '.format(phase_name) +
                        "of flow {}".format(flow_name))
                if spe_commit == phase_name:
                    raise ValueError(
                        'phase {} in flow {}'.format(phase_name, flow_name)\
                        + ' has a destination to itself in spe_commit')
        main_route, passed = _go_through_flow(start, flow)
        isolate = phase_names.difference(passed)
        if isolate:
            warnings.warn("never reach {}".format(isolate) +
                          " in flow {}".format(flow_name))
        print("main route in flow {}: {}".format(flow_name, main_route))


def _go_through_flow(start, flow, passed=None):
    initial = False
    route = list()
    if passed is None:
        initial = True
        passed = set()
    else:
        if start in passed:
            return
    current = start
    route.append(current)
    branches = set()
    while True:
        destination = flow[current]['destination']
        commit = destination['default']
        if commit is None:
            # The End
            break
        elif commit in passed:
            # we have gone through this phase
            if initial:
                raise ValueError('a circulate occurs {} in main'.format(route))
            return
        else:
            passed.add(commit)
            refuses = destination.get('refuse')
            if refuses:
                branches.update(refuses)
            spe_commits = destination.get('spe_commit')
            if spe_commits:
                branches.update(spe_commits)
            current = commit
            route.append(current)
    branches.difference_update(passed)
    for branch in branches:
        _go_through_flow(branch, flow, passed)
    if initial:
        return route, passed


if __name__ == '__main__':
    check_flows()
