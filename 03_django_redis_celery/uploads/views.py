# uploads/views.py

from django.shortcuts import render, redirect
from django.views import View
from .forms import FileUploadForm

class FileUploadView(View):
    def get(self, request):
        form = FileUploadForm()
        return render(request, 'uploads/upload.html', {'form': form})

    def post(self, request):
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('file_upload')
        return render(request, 'uploads/upload.html', {'form': form})