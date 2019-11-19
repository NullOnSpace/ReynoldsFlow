from django.apps import AppConfig


class FlowConfig(AppConfig):
    name = 'flow'

    def ready(self):
        from flow.flows import check_permissions
        check_permissions(auto_create=True)
