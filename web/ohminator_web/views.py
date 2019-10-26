import json
import os
from django.core.serializers.json import DjangoJSONEncoder
import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from ohminator_web.models import Guild, User, Plugin, Intro, IntroPlugin

from requests_oauthlib import OAuth2Session
from rest_framework.decorators import api_view
from rest_framework.response import Response

OAUTH2_CLIENT_ID = '315654415946219532'
OAUTH2_CLIENT_SECRET = 'I_UWW6KvtaRnQhIa7Wo4b5ubmgPyUoNA'
OAUTH2_REDIRECT_URI = 'http://127.0.0.1:8000/api/login'
GUILD_REDIRECT_URI = 'http://127.0.0.1:8000/api/bot_joined'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'


if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(request):
    if request is not None:
        def token_update(token):
            request.session['oauth2_token'] = token
        return token_update


def make_session(token=None, state=None, scope=None, request=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater(request))


@api_view(['GET'])
def get_me(request):
    discord = make_session(token=request.GET.get('oauth2_token'))
    if discord.authorized:
        return Response({'user': discord.get(API_BASE_URL + '/users/@me').json()})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def get_me_guilds(request):
    discord = make_session(token=request.GET.get('oauth2_token'))
    if discord.authorized:
        return Response({'guilds': discord.get(API_BASE_URL + '/users/@me/guilds').json()})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def get_user(request, user_id):
    discord = make_session(token=request.GET.get('oauth2_token'))
    if discord.authorized:
        return Response({'user': discord.get(API_BASE_URL + '/users/' + user_id).json()})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def get_guild(request, guild_id):
    discord = make_session(token=request.GET.get('oauth2_token'))
    if discord.authorized:
        guild, created = Guild.objects.get_or_create(id=guild_id)
        return Response({'guild': json.dumps(guild), 'plugins': get_guild_plugins(guild_id)})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def get_plugins(request, guild_id):
    discord = make_session(token=request.GET.get('oauth2_token'))
    if discord.authorized:
        plugins = get_guild_plugins(guild_id)
        return Response({'plugins': plugins})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def get_plugin(request, guild_id, plugin_name):
    discord = make_session(token=request.GET.get('oauth2_token'))
    if discord.authorized:
        try:
            # Fetch plugin data again, already fetched on guild dashboard (?)
            plugin_obj = Plugin.objects.filter(guild=Guild.objects.get(pk=guild_id)).filter(
                url_ending=plugin_name).get()
            from django.core import serializers
            data = json.loads(serializers.serialize('json', [*[plugin_obj], *[plugin_obj.plugin_ptr]]))

            return Response({'plugin': {'model': data[0]['model'],
                                        'fields': {**data[1]['fields'],
                                                   **data[0]['fields']}}})
        except Exception:
            return Response({'error': 'exception occurred'})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def plugins_status(request, guild_id):
    discord = make_session(token=request.GET.get('oauth2_token'))
    if discord.authorized:
        status_plugins = []
        plugins = Plugin.objects.all()
        for plugin in plugins:
            status_plugins.append({plugin.name, plugin.enabled})

        return Response({'plugins': json.dumps(status_plugins)})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def get_client(request):
    return Response({'client_id': OAUTH2_CLIENT_ID})


@api_view(['GET'])
def get_oauth_uri(request):
    return Response({'oauth_uri': "https://discordapp.com/oauth2/authorize?client_id=" +
                                  OAUTH2_CLIENT_ID +
                                  "&scope=bot&permissions=2146958591"})


def get_guild_plugins(guild_id):
    real_plugins = Plugin.objects.filter(guild=Guild.objects.get(pk=guild_id))

    # Fetching plugins
    plugin_list = []
    from django.core import serializers
    for plugin_obj in real_plugins:
        plugin_list.append(json.loads(serializers.serialize('json', [*[plugin_obj], *[plugin_obj.plugin_ptr]])))

    # Concatenate the two indexes (base+derived) to one (easier indexing on frontend)
    plugin_list_final = []
    for data in plugin_list:
        plugin_list_final.append({'model': data[0]['model'], 'fields': {**data[0]['fields'],
                                                                        **data[1]['fields']}})

    return plugin_list_final
