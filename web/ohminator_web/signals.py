from django.db.models.signals import post_save
from django.dispatch import receiver
from ohminator_web.models import Guild, IntroPlugin, YoutubePlugin


@receiver(post_save, sender=Guild)
def plugin_creater(sender, instance, **kwargs):
    IntroPlugin.objects.create(name="Intros", url_ending="intros", guild=instance)
    YoutubePlugin.objects.create(name="YouTube", url_ending="youtube", guild=instance)
