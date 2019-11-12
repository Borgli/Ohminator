import Cookies from "js-cookie";
import "regenerator-runtime/runtime";
import {put, select} from "redux-saga/effects";
import {getDiscordGuilds} from "../reducers/discordGuilds";
import {
    SET_BOT_GUILDS_FAILURE,
    SET_BOT_GUILDS_SUCCESS,
    SET_DISCORD_GUILDS_FAILURE,
    SET_DISCORD_GUILDS_SUCCESS,
    SET_GUILD_PLUGIN_FAILURE,
    SET_GUILD_PLUGIN_SUCCESS,
    SET_GUILD_POST_FAILURE,
    SET_GUILD_POST_SUCCESS,
    SET_USER_FAILURE,
    SET_USER_SUCCESS
} from "../reducers/actions";

const config = require('config');

export function* fetchUser(oauthCode) {
    yield fetchApi(oauthCode,
        (response) => ({type: SET_USER_SUCCESS, user: response.user}),
        (error) => ({type: SET_USER_FAILURE, error}),
        '/api/user');
}

export function* fetchGuilds(oauthCode) {
    yield fetchApi(oauthCode,
        (response) => ({type: SET_DISCORD_GUILDS_SUCCESS, guilds: response.guilds}),
        (error) => ({type: SET_DISCORD_GUILDS_FAILURE, error}),
        '/api/discord/guilds');

    const discordGuilds = yield select(getDiscordGuilds);
    const guilds = discordGuilds.map(guild => guild.id).join(',')

    yield fetchApi(oauthCode,
        (response) => ({type: SET_BOT_GUILDS_SUCCESS, guilds: response.guilds}),
        (error) => ({type: SET_BOT_GUILDS_FAILURE, error: error}),
        `/api/bot/guilds?guild_ids=${guilds}`
    );
}

export function* fetchGuildPlugins(id, oauthCode) {
    yield fetchApi(oauthCode,
        (response) => ({type: SET_GUILD_PLUGIN_SUCCESS, plugins: response.plugins}),
        (error) => ({type: SET_GUILD_PLUGIN_FAILURE, error}),
        `/api/plugins/${id}`
    );
}

export function* fetchApi(oauthCode, successAction, errorAction, uri) {
    let headers = {'Content-Type': 'application/json'};
    headers['X-Oauth-Code'] = oauthCode;

    try {
        const response = yield fetch(config.endpoint + uri, {headers})
            .then(response => response.json());
        yield put(successAction(response));
    } catch (error) {
        yield put(errorAction(error));
    }
}

export function* postGuild(id, oauthCode) {
    yield postApi(oauthCode,
        (response) => ({type: SET_GUILD_POST_SUCCESS}),
        (error) => ({type: SET_GUILD_POST_FAILURE}),
        '/api/bot/guilds',
        {guild: {id}}
    );
}

export function* postApi(oauthCode, successAction, errorAction, uri, data) {
    let headers = {'Content-Type': 'application/json'};
    headers['X-Oauth-Code'] = oauthCode;

    try {
        const response = yield fetch(
            config.endpoint + uri,
            {method: 'POST', headers, body: JSON.stringify(data)})
            .then(response => response.json());
        yield put(successAction(response))
    } catch (error) {
        yield put(errorAction(error));
    }
}

function postData(url = '', data = {}) {
    // Default options are marked with *
    return fetch(url, {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        credentials: "same-origin", // include, *same-origin, omit
        headers: {
            "Content-Type": "application/json",
            'X-CSRFToken': Cookies.get("csrftoken"),
            'Accept': "application/json"
            // "Content-Type": "application/x-www-form-urlencoded",
        },
        body: JSON.stringify(data), // body data type must match "Content-Type" header
    })
        .then(response => response.json()); // parses JSON response into native Javascript objects
}

export default postData;
