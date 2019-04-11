from django.apps import AppConfig


class OhminatorConfig(AppConfig):
    name = 'ohminator'

    # def ready(self):
    #     from ohminator.ohminator import main
    #     main()


class OhminatorWebConfig(AppConfig):
    name = 'ohminator_web'
