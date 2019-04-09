from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

# Create your models here.


class Channel(models.Model):
    app_label = "ohminator_web"
    id = models.CharField(max_length=18, primary_key=True)


class Guild(models.Model):
    id = models.CharField(max_length=18, primary_key=True)
    prefix = models.CharField(max_length=2, default='!')


class Plugin(models.Model):
    communication = models.CharField(max_length=2, choices=(('DM', 'Direct Message'), ('CH', Channel),
                                                            ('U', "Respond to user channel"), ("M", "Muted")),
                                     default='U')
    enabled = models.BooleanField(default=False)
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class IntroPlugin(Plugin):
    name = models.CharField(max_length=50, editable=False, default="Intro Plugin")
    pass


class User(models.Model):
    id = models.CharField(max_length=18, primary_key=True)
    guilds = models.ManyToManyField(Guild)

