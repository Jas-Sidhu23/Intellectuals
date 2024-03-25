from django.shortcuts import render, redirect
from .forms import ProductForm

def index(request):
    return render(request, 'index.html')

def signin(request):
    # Logic for signin
    return render(request, 'signin.html')

def signup(request):
    # Logic for signup
    return render(request, 'signup.html')

def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Redirect to product list page after successful addition
    else:
        form = ProductForm()
    return render(request, 'add_product.html', {'form': form})