from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save

from polymorphic.models import PolymorphicModel


# Create your models here.


class Channel(models.Model):
    app_label = "ohminator_web"
    id = models.CharField(max_length=18, primary_key=True)


class Guild(models.Model):
    id = models.CharField(max_length=18, primary_key=True)
    prefix = models.CharField(max_length=2, default='!')


class Plugin(PolymorphicModel):
    name = models.CharField(max_length=50, null=False)
    communication = models.CharField(max_length=2, choices=(('DM', 'Direct Message'), ('CH', Channel),
                                                            ('U', "Respond to user channel"), ("M", "Muted")),
                                     default='U')
    enabled = models.BooleanField(default=False)
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, null=False)

    # class Meta:
    #     abstract = True


class IntroPlugin(Plugin):
    pass


class AudioPlugin(Plugin):
    pass


class Oauth(models.Model):
    oauth_code = models.CharField(max_length=30, primary_key=True)
    token_type = models.CharField(max_length=6)
    access_token = models.CharField(max_length=30)
    expires_in = models.PositiveIntegerField()
    refresh_token = models.CharField(max_length=30)
    scope = models.CharField(max_length=50)


class User(models.Model):
    id = models.CharField(max_length=18, primary_key=True)
    guilds = models.ManyToManyField(Guild)


class Intro(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    guilds = models.ManyToManyField(Guild)
    intro = models.FileField(null=False)
