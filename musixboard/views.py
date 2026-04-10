from django.shortcuts import render

def board(request):
    return render(request, 'mboard.html')