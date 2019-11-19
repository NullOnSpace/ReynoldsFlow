from django.contrib import admin
from .models import Flow, Node, User


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    exclude = ('password',)

admin.site.register(Flow)
admin.site.register(Node)
