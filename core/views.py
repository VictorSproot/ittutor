from django.shortcuts import render, redirect
from django.views import View
from main.models import Bb












def error_404(request, exception, template_name='404.html'):
    return render(request, template_name, status=404)