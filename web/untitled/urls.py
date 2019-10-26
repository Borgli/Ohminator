"""untitled URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

from web.ohminator_web.views import login, logout, index, dashboard, guild_joined_successful, \
    guild_dashboard, server_selected, get_plugin, plugins_status, get_plugins, get_me, get_me_guilds, get_user, get_guild, get_client

import web.ohminator_web.signals

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login', login),
    path('api/logout', logout),
    path('api/user', get_me),
    path('api/guilds', get_me_guilds),
    path('api/guilds/<int:guild_id>', get_guild),
    path('api/plugins/<int:guild_id>/', get_plugins),
    path('api/plugins/<int:guild_id>/<str:plugin_name>', get_plugin),
    path('api/plugins/<int:guild_id>/plugins_status', plugins_status),
    path('api/user/<int:user_id>', get_user),
    path('api/client', get_client),
    path('dashboard/<int:guild_id>', guild_dashboard, name="guild_dashboard"),
    path('dashboard/<int:guild_id>/', RedirectView.as_view(pattern_name='guild_dashboard', permanent=True)),
    path('dashboard', dashboard, name="dashboard"),
    path('dashboard/', RedirectView.as_view(pattern_name="dashboard", permanent=True)),
    path('api/bot_joined', guild_joined_successful),
    path('api/guild/<int:guild_id>', server_selected),
    path('', index)
]
