from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.core.files.storage import FileSystemStorage


# Create your models here.
class DrawingNode(models.Model):
    STATUS = (
        (0, "检出"),
        (1, "检入"),
        (2, "完成"),
        (3, "废弃"),
        (4, "保留"),
        (5, "保留"),
    )
    name = models.CharField(max_length=30, unique=True)
    status = models.PositiveSmallIntegerField(choices=STATUS, default=0)
    is_deleted = models.BooleanField(default=False)
    create = models.DateTimeField(auto_now_add=True)
    abandon = models.DateTimeField(null=True, blank=True)
    flows = models.ManyToManyField('flow.Flow', through='DrawingNodeFlowRel')

    def __str__(self):
        return self.name


class Drawing(models.Model):
    STORAGE = FileSystemStorage(location='E://drawings', base_url='/media')

    order = models.PositiveSmallIntegerField()
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    location = models.FileField(upload_to='drawing/%Y/%m/%d/', storage=STORAGE)
    drawing_node = models.ForeignKey(DrawingNode, on_delete=models.CASCADE)
    create = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    deleted_dt = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.location.name if self.location else "unbound drawing"


class DrawingNodeFlowRel(models.Model):
    flow = models.ForeignKey('flow.Flow', on_delete=models.CASCADE,
                             related_name='drawings')
    drawing_node = models.ForeignKey('DrawingNode', on_delete=models.CASCADE)
    create = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return '{} - {}'.format(self.flow.name, self.drawing_node.name)
