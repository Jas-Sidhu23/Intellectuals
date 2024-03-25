from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def signin(request):
    # Logic for signin
    return render(request, 'signin.html')

def signup(request):
    # Logic for signup
    return render(request, 'signup.html')