from django.shortcuts import render

def index(request):
    return render(request, 'vuelos/index.html')