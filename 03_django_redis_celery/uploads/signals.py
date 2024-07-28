# uploads/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UploadedFile
from .tasks import process_file_metadata

@receiver(post_save, sender=UploadedFile)
def trigger_metadata_processing(sender, instance, created, **kwargs):
    if created:
        process_file_metadata.delay(instance.id)
        