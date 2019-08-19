from django.template import Library


register = Library()


@register.simple_tag
def stag1():
    return str()
