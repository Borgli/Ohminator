from django.db.models.signals import post_save
from django.dispatch import receiver
from ohminator_web.models import Guild, IntroPlugin


@receiver(post_save, sender=Guild)
def plugin_creater(sender, instance, **kwargs):
    IntroPlugin.objects.create(guild=instance)
