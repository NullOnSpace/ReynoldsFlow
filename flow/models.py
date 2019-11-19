from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

from .flows import FLOWS


# Create your models here.
class User(AbstractUser):
    pass


class Flow(models.Model):
    FLOW_STATUS = (
        (0, '未指派'), (1, '进行中'), (2, '已结束'), (3, '已冻结'),
        (4, '预留4'),
    )

    # flow's name created by sponsor of this flow instance
    name = models.CharField(max_length=150, unique=True)
    # flow_name in the FLOWS in flows.py
    flow_name = models.CharField(max_length=50)
    status = models.SmallIntegerField(choices=FLOW_STATUS, default=0)
    head_node = models.OneToOneField("Node",
                                     related_name="sequence_flow",
                                     null=True, blank=True,
                                     on_delete=models.CASCADE)
    sponsor = models.ForeignKey(User, on_delete=models.CASCADE)
    create = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    desc = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{} - {} - {}".format(
            self.name, self.get_status_display(), self.flow_name,
        )

    def get_absolute_url(self):
        if self.head_node is None:
            return reverse("init_flow", args=(self.pk,))
        else:
            return reverse("show_flow", args=(self.pk,))

    def get_node_list(self):
        node_list = list()
        if self.head_node:
            node = self.head_node
            while node:
                node_list.append(node)
                node = node.next_node
        return node_list

    @property
    def definition(self):
        return FLOWS.get(self.flow_name)


class Node(models.Model):
    NODE_STATUS = (
        (0, '未接受'), (1, '已接受'), (2, '已提交'), (3, '已转交'),
        (4, '已驳回'), (5, '已特殊提交'), (6, '预留六'), (7, '预留七'),
    )

    # node name in FLOWS of flows.py
    name = models.CharField(max_length=50)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    create = models.DateTimeField(auto_now_add=True)
    accept = models.DateTimeField(null=True, blank=True)
    status = models.SmallIntegerField(choices=NODE_STATUS, default=0)
    note = models.TextField(null=True, blank=True)
    end = models.DateTimeField(auto_now=True)
    next_node = models.OneToOneField('self',
                                     related_name='previous_node',
                                     null=True, blank=True,
                                     on_delete=models.CASCADE)
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE)
    order = models.SmallIntegerField()

    def __str__(self):
        return "{}:{} - {}".format(
            self.name, self.get_status_display(), self.flow)

    def get_absolute_url(self):
        return reverse("show_node", args=(self.pk,))

    @property
    def definition(self):
        flow_dict = FLOWS.get(self.flow.flow_name)
        if flow_dict:
            return flow_dict['flow'].get(self.name)
        return None
