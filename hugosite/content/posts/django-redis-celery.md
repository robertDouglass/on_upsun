+++
title = 'Background Tasks using Celery with Redis in Django on Upsun'
date = 2024-07-28T11:00:00+02:00
draft = false
+++

In this post I show a minimal Django application that runs on Upsun. It has a PostgreSQL database, a Python Gunicorn application server, a Gunicorn Worker that runs Celery tasks, and a Redis server that manages the state of the Celery queue. I recommend reading [my previous two articles](https://robertdouglass.github.io/on_upsun/posts/install-django-sqlite-upsun/) on [running Django on Upsun](https://robertdouglass.github.io/on_upsun/posts/install-django-postgresql-pgvector-upsun/) for information on how to get this code deployed.

This Django appplication is simple, with a single file upload field. When a file is uploaded, a Celery background worker receives a signal to extract and persist the metadata of the file. This keeps potentially heavy computing tasks out of the user-facing HTTP request and lets them run in the background. Then, every minute (this can be an arbitrary interval), the Celery worker collects all of the metadata from all of the files that have been uploaded and sends a report about them in an email.

This small app shows the following very powerful patterns:

1. Extending Django behavior with Signals
2. Using Celery Queue and Beat to run background tasks 
3. Creating Workers with shared file system mounts on Upsun
4. Running Redis on Upsun

The full application code is here.

## Extending Django behavior with Signals

Django signals allow decoupled applications to get notified when actions occur elsewhere in the framework. Django components can then communicate without tight coupling. Signals are dispatched by senders, eg. from models or forms. For instance, the `post_save` signal can be used to trigger actions after a model instance is saved. You can then definine a signal handler function, connecting it to a signal using the `@receiver` decorator, and performing specific tasks when the signal is sent​​​​​​​​.

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

The key line here is `form.save()`. This is where the "sending" of the signal happens, although it's happening behind the scenes:

1. When `form.save()` is called, it creates and saves a new `UploadedFile` instance to the database.
2. Django's ORM automatically sends a `post_save` signal when any model instance is saved.

Here is the `@receiver` decorator that identifies this function as receiving the signal above. 

```python
# uploads/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UploadedFile
from .tasks import process_file_metadata

@receiver(post_save, sender=UploadedFile) # This decorator defines the receiver
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

The `uploader` app defines two tasks. One that responds to the file upload signal that was just shown, and another that functions like a cron job and executes at an interval (1 minute in the example app). I will first discuss how the Django code works, and then I'll show what is involved in setting this up on Upsun.

```python
# uploads/signals.py
...
@receiver(post_save, sender=UploadedFile) 
def trigger_metadata_processing(sender, instance, created, **kwargs):
    if created:
        process_file_metadata.delay(instance.id) # This triggers Celery
```

The call to `delay()` in this code is what triggers the first background process. Here is the essence of the `uploader/tasks.py` file, where the Celery tasks are defined:

```python
@shared_task # This decorator identifies the function as a Celery task
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
    
@shared_task # This decorator identifies the function as a Celery task
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

A function decorated with `@shared_task` turns into a task that can be added to the Celery task queue. It allows the function to be called asynchronously using methods like `.delay()` or `.apply_async()`.

### Sharing file mounts with the parent application

Second, and perhaps less obvious on first reading, is the implicit expectation that the worker process has access to the same file system mounts as the parent application:

```python
@shared_task
def process_file_metadata(file_id):
    # Get the metadata
    uploaded_file = UploadedFile.objects.get(id=file_id) 
    file_path = uploaded_file.file.path # This expects a file on the file system
```

The `file_path` is going to be the same no matter what process is running this code. However, on Upsun, the Celery process is going to run in its own container, separate from the main application container. 

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
      "media": # This is where our files are getting uploaded
        source: "storage"
        source_path: "media"

# stuff omitted for brevity ...

    workers:
      queue:
        mounts:
          "media": # This will be shared with the app listed in `service` - "uploader" in this case
            source: "storage"
            source_path: "media"
            service: "uploader" # This is the name of the parent app for inheritance
        commands:
          start: |
            celery -A file_uploader worker -B --loglevel=info
```
### Django settings

Celery won't run without proper configuration in Django's `settings.py` file. In this app, you'll find the Celery and Redis configuration in the `settings_psh.py`, which are the Upsun specific extensions to the settings.py file. 

```python
CELERY_BROKER_URL = CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    'send-file-report-every-minute': {
        'task': 'uploads.tasks.send_file_report',
        'schedule': crontab(minute='*'),
    },
```

For the Redis setup, see the section "Running Redis on Upsun" below. 

### Watch Celery in action

From your command line, open a shell on the Celery container like this:

```bash
upsun ssh --worker=queue
```
You're then in the environment of the Celery `queue` worker, which is responsible for responding to signals sent by uploaded files in order to process the metadata of the file. Assuming you've visited your application running on Upsun and have uploaded a file:

```bash
web@uploader--queue.0:~$ tail -f /var/log/app.log | grep Uploader
[2024-07-28 17:02:21,673: INFO/ForkPoolWorker-8] Uploader: Starting to process metadata for file with id: 4
[2024-07-28 17:02:21,749: INFO/ForkPoolWorker-8] Uploader: Successfully processed metadata for file: /app/media/uploads/01_settings_psh_error_mUr16sP.png
[2024-07-28 17:03:00,052: INFO/ForkPoolWorker-8] Uploader: Starting to send file report
[2024-07-28 17:03:00,113: INFO/ForkPoolWorker-8] Uploader: Sending file report: robert@openstrategypartners.com
```

## Running Redis on Upsun

Running Redis on Upsun is so easy it's almost not worth mentioning =)

It starts with the `.upsun/config.yaml`:

```yaml
applications:
  uploader:
    source:
      root: "/file_uploader/"
    type: "python:3.12"

    relationships:
      postgresql:
      redis: # This line ensures that the application (uploader) container can talk to the Redis container
...

services:
  postgresql:
    type: postgresql:15
  redis: # These two lines are enough to ensure a Redis container is deployed
    type: redis:7.0
```

Then, in `settings_psh.py`, the essence of the code is this:

```python
platform_relationships = decode(os.getenv("PLATFORM_RELATIONSHIPS"))      
redis_settings = platform_relationships['redis'][0]
REDIS_HOST = redis_settings['host']
REDIS_PORT = redis_settings['port']
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
```

Here are some things to try to play with Redis.

```bash
upsun service:redis-cli
Connecting to Redis service via relationship redis on cetuuybazrhns-main-bvxea6i--uploader@ssh.ca-1.platform.sh
redis.internal:6379> PING
PONG
redis.internal:6379> INFO
# Server
redis_version:7.0.15
...

redis.internal:6379> KEYS *
  1) "celery-task-meta-3b1b785f-6e86-472f-b21e-e4b9f6c737eb"
  2) "celery-task-meta-c3c53189-0ed3-48e0-b845-40ae9eef797e"
  3) "celery-task-meta-b305e465-c534-407c-96e5-ca1d691ac8b4"
  ```

  ## Conclusion

This Django application showcases the integration of Celery and Redis on Upsun for efficient background task processing. By utilizing Django signals, Celery tasks, and Upsun's flexible container configuration, we've created a scalable system that handles file uploads, metadata processing, and scheduled reporting. This architecture demonstrates how to build Django applications on Upsun that can manage complex operations without impacting user experience.

Thanks for reading the tutorial! If you have any questions, my email address is rob@robshouse.net and you can [find me on LinkedIn](https://www.linkedin.com/in/roberttdouglass/). There is also an [Upsun Discord forum](https://discord.gg/PkMc2pVCDV) where I hang out, and you're welcome to find me there.


