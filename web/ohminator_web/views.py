import json
import os

from django.shortcuts import render, redirect
from ohminator_web.models import Server

from requests_oauthlib import OAuth2Session

OAUTH2_CLIENT_ID = '315654415946219532'
OAUTH2_CLIENT_SECRET = 'I_UWW6KvtaRnQhIa7Wo4b5ubmgPyUoNA'
OAUTH2_REDIRECT_URI = 'http://127.0.0.1:8000/api/oauth_success'

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


def authentication_successful(request):
    # Get Auth Token
    if request.GET.get('error'):
        return request.GET['error']
    discord = make_session(state='', request=request)
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.get_raw_uri())
    request.session['oauth2_token'] = token
    print(token)
    return redirect('/dashboard', permanent=True)


def dashboard(request):
    # Get user info
    discord = make_session(token=request.session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    print(user)
    return render(request, "ohminator_web/dashboard.html", {"user": json.dumps(user), "guilds": json.dumps(guilds)})


def index(request):
    return render(request, "ohminator_web/index.html")


def guild_joined_successful(request):
    discord = make_session(token=request.session.get('oauth2_token'))
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    guild = list(filter(lambda g: g["id"] == request.GET.get('guild_id'), guilds)).pop()
    print(guild)
    return redirect("/dashboard/" + guild['id'])
