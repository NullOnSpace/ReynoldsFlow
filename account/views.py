from django.shortcuts import render
from django.contrib.auth.views import LoginView, LogoutView


# Create your views here.
class UserLogin(LoginView):
    pass


class UserLogout(LogoutView):
    pass
