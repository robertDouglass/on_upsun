+++
title = 'Background Tasks using Celery with Redis in Django on Upsun'
date = 2024-07-28T11:00:00+02:00
draft = false
+++

In this post I show a minimal Django application that runs on Upsun. It has a PostgreSQL database, a Python Gunicorn application server, a Gunicorn Workers that runs Celery tasks, and a Redis server that manages the state of the Celery queue. I recommend reading [my previous two articles](https://robertdouglass.github.io/on_upsun/posts/install-django-sqlite-upsun/) on [running Django on Upsun](https://robertdouglass.github.io/on_upsun/posts/install-django-postgresql-pgvector-upsun/) for information on how to get this code deployed.

The Django appplication is simple, with a single file upload field. When a file is uploaded, a Celery background worker receives a signal to extract and persist the metadata of the file. This keeps potentially heavy computing tasks out of the user-facing HTTP request and lets them run in the background. Then, every minute (this can be an arbitrary interval), the Celery worker collects all of the metadata from all of the files that have been uploaded and sends a report about them in an email.

This small app shows the following very powerful patterns:

1. Extending Django behavior with Signals
2. Using Celery Queue and Beat to run background tasks 
3. Creating Workers with shared file system mounts on Upsun
4. Running Redis on Upsun

The full application code is here. To install it .... 

## Extending Django behavior with Signals

Django signals allow decoupled applications to get notified when actions occur elsewhere in the framework. Django components can then communicate without tight coupling. Signals are dispatched by senders, eg. from models or forms. For instance, the post_save signal can be used to trigger actions after a model instance is saved. You can then definine a signal handler function, connecting it to a signal using the @receiver decorator, and performing specific tasks when the signal is sent​​​​​​​​.

In my code, signals are being used to automatically trigger actions when files are uploaded:

In `views.py`, the "sender" action is present, although it's not explicitly called out:

```python
pythonCopyclass FileUploadView(View):
    # ... (get method omitted for brevity)

    def post(self, request):
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()  # This is where the signal is triggered
            return redirect('file_upload')
        return render(request, 'uploads/upload.html', {'form': form})
```

The key line here is form.save(). This is where the "sending" of the signal happens, although it's happening behind the scenes:

1. When form.save() is called, it creates and saves a new UploadedFile instance to the database.
2. Django's ORM automatically sends a post_save signal when any model instance is saved.

Here is the `@receiver` decorator that identifies this function as receiving the signal above. 

```python
# uploads/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UploadedFile
from .tasks import process_file_metadata

@receiver(post_save, sender=UploadedFile) # This defines the receiver
def trigger_metadata_processing(sender, instance, created, **kwargs):
    if created:
        process_file_metadata.delay(instance.id)
```
For this signal to work, it needs to be imported and registered when Django starts. This is done in apps.py:

```python
# uploads/apps.py

pythonCopyfrom django.apps import AppConfig

class UploadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'uploads'

    def ready(self): # Register the signal
        import uploads.signals
```

And in the app's` __init__.py`:

```python
# uploads/__init__.py
pythonCopydefault_app_config = 'uploads.apps.UploadsConfig'
```
The code shown so far is enough to capture the signal of a file being uploaded and turn it over to Celery.

## Using Celery Queue and Beat to run background tasks

The `uploader` app defines two Celery workers. One that responds to the file upload signal that was just shown, and another that functions like a cron job and executes at an interval (1 minute in the example app). I will first discuss how the Django code works, and then I'll show what is involved in setting this up on Upsun.

```python
# uploads/signals.py
...
@receiver(post_save, sender=UploadedFile) # This defines the receiver
def trigger_metadata_processing(sender, instance, created, **kwargs):
    if created:
        process_file_metadata.delay(instance.id) 
```

The call to `delay()` in this code is what triggers the first background process. Here is the essence of the `uploader/tasks.py` file:

```python
@shared_task
def process_file_metadata(file_id):
    # Get the metadata
    uploaded_file = UploadedFile.objects.get(id=file_id)
    file_path = uploaded_file.file.path
    metadata = {
        'name': os.path.basename(file_path),
        'size': os.path.getsize(file_path),
    }
    # Save the metadata
    uploaded_file.metadata = metadata
    uploaded_file.save()
    
@shared_task
def send_file_report():
        # Get info on the uploaded files
        files = UploadedFile.objects.all()
        # Make a report
        report = "Uploaded Files:"
        for file in files:
            report += f"File: {file.file.name}\n"
            ...
        # Send the report
        send_mail(
            ...
        )
```

The code in the tasks is unremarkable except for two important details. 

### The @shared_task decorator

First, the `@shared_task` decorator is a feature provided by Celery. It marks a function as a task that can be run asynchronously by Celery. It also allows the task to be used in any application that imports it, not just the application where it's defined.

A function decorated with @shared_task turns into a task that can be added to the Celery task queue. It allows the function to be called asynchronously using methods like .delay() or .apply_async().

### Sharing file mounts with the parent application

Second, and perhaps less obvious on first reading, is the implicit expectation that the worker process has access to the same file system mounts as the parent application:

```python
@shared_task
def process_file_metadata(file_id):
    # Get the metadata
    uploaded_file = UploadedFile.objects.get(id=file_id)
    file_path = uploaded_file.file.path
```

The `file_path` is going to be the same no matter what process is running this code. However, on Upsun, the Celery process is going to run in its own container. 

## Creating Workers with shared file system mounts on Upsun

Now that we understand that the Celery worker will need to access the same file system as the parent app while running in a different container, the Upsun configuration for creating Workers will make more sense. 

```yaml
# .upsun/config.yaml
applications:
  uploader: # Note this... it's the name of the application. It becomes the `service` value in Workers
    source:
      root: "/file_uploader/"

    type: "python:3.12"

    relationships:
      postgresql:
      redis:

    mounts:
      "media":
        source: "storage"
        source_path: "media"

# stuff omitted for brevity ...

    workers:
      queue:
        mounts:
          "media":
            source: "storage"
            source_path: "media"
            service: "uploader" # This is the name of the parent app for inheritance
        commands:
          start: |
            celery -A file_uploader worker -B --loglevel=info
```


```bash
upsun ssh --worker=queue
```
You're then in the environment of the Celery `queue` worker, which is responsible for responding to signals sent by uploaded files in order to process the metadata of the file. 

```bash
web@uploader--queue.0:~$ tail -f /var/log/app.log

... example logs from when a file was uploaded
[2024-07-27 18:33:26,875: INFO/MainProcess] Task uploads.tasks.process_file_metadata[238a279a-0e41-4d32-848f-2fd3399532e0] received
[2024-07-27 18:33:26,878: INFO/ForkPoolWorker-1] Starting to process metadata for file with id: 5
[2024-07-27 18:33:26,934: INFO/ForkPoolWorker-1] Successfully processed metadata for file: /app/media/uploads/image_1000px.jpg
```


beat

```bash
[2024-07-27 18:59:00,020: INFO/MainProcess] Scheduler: Sending due task send-file-report-every-minute (uploads.tasks.send_file_report)
```

