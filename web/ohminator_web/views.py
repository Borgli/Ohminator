import json
import os
import requests
from django.http import HttpResponseNotFound, Http404
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from requests.exceptions import HTTPError

from ohminator_web.models import Guild, User, Plugin, Intro, IntroPlugin, Oauth

from rest_framework.decorators import api_view
from rest_framework.response import Response

OAUTH2_CLIENT_ID = '639373877381693463'
OAUTH2_CLIENT_SECRET = 'ZMjOzpysTgwlukG1EjbccN5n9A6MW75o'
OAUTH2_REDIRECT_URI = 'https://localhost:8000/api/login'
GUILD_REDIRECT_URI = 'http://localhost:8000/api/bot_joined'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def exchange_code(code):
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': OAUTH2_CLIENT_ID,
        'client_secret': OAUTH2_CLIENT_SECRET,
        'redirect_uri': OAUTH2_REDIRECT_URI,
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    url = '%s/oauth2/token' % API_BASE_URL

    r = requests.post(url, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


def get_token(code):
    if Oauth.objects.filter(oauth_code=code).exists():
        return Oauth.objects.get(oauth_code=code).access_token

    oauth_object = exchange_code(code)
    Oauth(oauth_code=code,
          access_token=oauth_object['access_token'],
          token_type=oauth_object['token_type'],
          expires_in=oauth_object['expires_in'],
          refresh_token=oauth_object['refresh_token'],
          scope=oauth_object['scope']).save()
    return oauth_object['access_token']


def api_call(uri, code, tag):
    try:
        token = get_token(code)
    except HTTPError as error:
        return Response({'error': error.response.status_code})

    headers = {'Authorization': 'Bearer %s' % token}

    try:
        r = requests.get('%s%s' % (API_BASE_URL, uri), headers=headers)
        r.raise_for_status()
        return Response({tag: r.json()})
    except requests.exceptions.HTTPError as error:
        return Response({'error': error.response.status_code})


def make_session():
    return None


@api_view(['GET'])
def user(request):
    code = request.headers["X-Oauth-Code"]
    return api_call('/users/@me', code, 'user')


@api_view(['GET', 'POST', 'PUT'])
def guilds(request):
    # Authentication check
    code = request.headers["X-Oauth-Code"]
    if not Oauth.objects.filter(oauth_code=code).exists():
        raise PermissionDenied

    if request.method == 'GET':
        return api_call('/users/@me/guilds', code, 'guilds')

    if request.method in ['PUT', 'POST']:
        guild = request.data['guild']
        print(request.data)
        guild_id = guild['id']
        Guild(id=guild_id, prefix='!').save()
        guild = Guild.objects.get(id=guild_id)
        return Response({'guild': json.dumps(guild)})



@api_view(['GET'])
def get_user(request, user_id):
    discord = make_session()
    if discord.authorized:
        return Response({'user': discord.get(API_BASE_URL + '/users/' + user_id).json()})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def get_guild(request, guild_id):
    code = request.headers["X-Oauth-Code"]
    if not Oauth.objects.filter(oauth_code=code).exists():
        return Response({'error': 'not authorized'})

    if Guild.objects.filter(id=guild_id).exists():
        guild = Guild.objects.get(id=guild_id)
        return Response({'guild': json.dumps(guild)})
    else:
        return HttpResponseNotFound('<h1>Guild not found</h1>')


@api_view(['GET'])
def get_plugins(request, guild_id):
    discord = make_session()
    if discord.authorized:
        plugins = get_guild_plugins(guild_id)
        return Response({'plugins': plugins})
    else:
        return Response({'error': 'not authorized'})


@api_view(['GET'])
def get_plugin(request, guild_id, plugin_name):
    discord = make_session()
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
    discord = make_session()
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
    return Response({'clientID': OAUTH2_CLIENT_ID})


@api_view(['GET'])
def get_oauth_bot_uri(request):
    return Response({'oauthUri': "https://discordapp.com/oauth2/authorize?client_id=" +
                                 OAUTH2_CLIENT_ID +
                                 "&scope=bot&permissions=2146958591"})


@api_view(['GET'])
def get_oauth_user_uri(request):
    return Response({'oauthUri': "https://discordapp.com/oauth2/authorize?client_id=" +
                                 OAUTH2_CLIENT_ID +
                                 "&scope=identify%20email%20guilds"})


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
