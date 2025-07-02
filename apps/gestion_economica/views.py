from django.shortcuts import render

def index(request):
    return render(request, 'gestion_economica/index.html')