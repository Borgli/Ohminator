from django.db import models

# Create your models here.


class Channel(models):
    id = models.CharField(max_length=18)


class Plugin(models):
    name = models.CharField(max_length=50)
    communication = models.CharField(max_length=2, choices=(('DM', 'Direct Message'), ('CH', Channel),
                                                            ('U', "Respond to user channel"), ("M", "Muted")))


class Servers(models):
    id = models.CharField(max_length=18)
    prefix = models.CharField(max_length=2)
    plugins = models.ManyToManyField(Plugin)


class User(models):
    pass

