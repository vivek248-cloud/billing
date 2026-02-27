from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver
from .models import SiteImage
import os

@receiver(post_delete, sender=SiteImage)
def delete_site_image_file(sender, instance, **kwargs):
    # Delete the file from the filesystem when the SiteImage object is deleted
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)

@receiver(pre_save, sender=SiteImage)
def delete_old_image_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # Skip if the instance is new

    try:
        old_image = SiteImage.objects.get(pk=instance.pk).image
    except SiteImage.DoesNotExist:
        return

    new_image = instance.image
    if old_image and old_image != new_image:
        if os.path.isfile(old_image.path):
            os.remove(old_image.path)
