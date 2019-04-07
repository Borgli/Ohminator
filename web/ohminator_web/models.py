from django.db import models

# Create your models here.


class Channel(models.Model):
    app_label = "ohminator_web"
    id = models.CharField(max_length=18, primary_key=True)


class Plugin(models.Model):
    name = models.CharField(max_length=50)
    communication = models.CharField(max_length=2, choices=(('DM', 'Direct Message'), ('CH', Channel),
                                                            ('U', "Respond to user channel"), ("M", "Muted")))


class Server(models.Model):
    id = models.CharField(max_length=18, primary_key=True)
    prefix = models.CharField(max_length=2)
    plugins = models.ManyToManyField(Plugin)


class User(models.Model):
    pass

