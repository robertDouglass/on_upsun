# uploads/tasks.py

import os
import magic
import mimetypes
import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import UploadedFile

# Set up logger
logger = logging.getLogger(__name__)

@shared_task
def process_file_metadata(file_id):
    logger.info(f"Uploader: Starting to process metadata for file with id: {file_id}")
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id)
        file_path = uploaded_file.file.path
        
        logger.debug(f"Processing file: {file_path}")
        
        metadata = {
            'name': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'mime_type': magic.from_file(file_path, mime=True),
            'extension': os.path.splitext(file_path)[1],
        }
        
        uploaded_file.metadata = metadata
        uploaded_file.save()
        
        logger.info(f"Uploader: Successfully processed metadata for file: {file_path}")
    except UploadedFile.DoesNotExist:
        logger.error(f"Uploader: File with id {file_id} does not exist")
    except Exception as e:
        logger.error(f"Uploader: Error processing metadata for file {file_id}: {str(e)}")

@shared_task
def send_file_report():
    logger.info("Uploader: Starting to send file report")
    try:
        files = UploadedFile.objects.all()
        report = "Uploaded Files:\n\n"
        
        for file in files:
            report += f"File: {file.file.name}\n"
            report += f"Uploaded at: {file.uploaded_at}\n"
            report += f"Metadata: {file.metadata}\n\n"
        
        logger.info(f"Uploader: Sending file report: {settings.EMAIL_HOST_USER} \n {report}")

        send_mail(
            'File Upload Report',
            report,
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )
        
        logger.info(f"Uploader: Successfully sent file report: {settings.EMAIL_HOST_USER} \n {report}")
    except Exception as e:
        logger.error(f"Uploader: Error sending file report: {str(e)}")