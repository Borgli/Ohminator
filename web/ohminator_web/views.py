import json
import os

import requests
from django.shortcuts import render, redirect
from ohminator_web.models import Guild, User, Plugin

from requests_oauthlib import OAuth2Session

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


def login(request):
    # Get Auth Token
    if request.GET.get('error'):
        return redirect("/api/logout")
    discord = make_session(state='', request=request)
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.get_raw_uri())
    request.session['oauth2_token'] = token
    print(token)
    return redirect('/dashboard')


def logout(request):
    if 'oauth2_token' in request.session:
        del(request.session['oauth2_token'])
    return redirect('/')


def dashboard(request):
    # Get user info
    discord = make_session(token=request.session.get('oauth2_token', ''))
    if discord.authorized:
        discord_json = {
            'user': discord.get(API_BASE_URL + '/users/@me').json(),
            'guilds': discord.get(API_BASE_URL + '/users/@me/guilds').json(),
            'selected_guild': None
        }
        return render(request, "ohminator_web/dashboard.html", {"discord": json.dumps(discord_json)})
    else:
        return redirect("/api/logout")


def index(request):
    discord = make_session(token=request.session.get('oauth2_token', ''))
    if discord.authorized:
        discord_json = {
            'user': discord.get(API_BASE_URL + '/users/@me').json(),
            'guilds': None,
            'selected_guild': None
        }
        return render(request, "ohminator_web/dashboard.html", {"discord": json.dumps(discord_json)})
    else:
        return render(request, "ohminator_web/dashboard.html", {"discord": json.dumps(None)})


def guild_joined_successful(request):
    if request.GET.get('error'):
        return redirect("/dashboard")
    return redirect('/dashboard/' + request.GET.get('guild_id'))


def guild_dashboard(request, guild_id):
    discord = make_session(token=request.session.get('oauth2_token'))
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    selected_guild = list(filter(lambda g: g["id"] == str(guild_id), guilds)).pop()
    discord_json = {
        'user': discord.get(API_BASE_URL + '/users/@me').json(),
        'guilds': None,
        'selected_guild': selected_guild
    }

    dbguild, created = Guild.objects.get_or_create(id=guild_id)

    return render(request, "ohminator_web/dashboard.html", {"discord": json.dumps(discord_json)})


def server_selected(request, guild_id):
    # Check if guild exists in database
    try:
        Guild.objects.get(pk=guild_id)
        return redirect('/dashboard/' + str(guild_id))
    except Guild.DoesNotExist:
        return redirect("https://discordapp.com/oauth2/authorize?scope=bot&response_type=code&redirect_uri="
                        + GUILD_REDIRECT_URI + "&permissions=66321471&client_id=" + OAUTH2_CLIENT_ID + "&guild_id="
                        + str(guild_id))