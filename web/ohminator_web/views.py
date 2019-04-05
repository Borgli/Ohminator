from django.shortcuts import render

# Create your views here.


def login(request):
    pass


def authentication_successful(request, poll_id):
    render(request, "dashboard.html")
