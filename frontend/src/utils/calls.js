import Cookies from "js-cookie";
import {updateDiscord, updatePluginPagem,
    updateOauthUserUri, updateOauthBotUri} from "../actions";

const endpoint = 'http://127.0.0.1:8000';

const guildEndpoint = endpoint + '/api/guild/';
const dashboardEndpoint = endpoint + '/dashboard/';


export const getGuildPlugins = (guild) => {
    fetch(`${guildEndpoint}${guild.id}/plugins`)
        .then(response => response.json())
        .then(result => dispatch(updateDiscord(result)));
};

export const getGuildPluginInfo = (url='') => {
    fetch(endpoint + url, {})
        .then(response => response.json())
        .then((result) => {
            const discord = JSON.parse(result.data.discord);
            this.props.dispatch(updatePluginPage(this.props.plugin.model, discord));
        })
};

export const getOauthUserUri = () => {
    fetch('/api/oauth_user_uri')
      .then(response => response.json())
      .then(result => dispatch(updateOauthUserUri(result.oauthUri)))
};

export const getOauthBotUri = () => {
    fetch('/api/oauth_bot_uri')
      .then(response => response.json())
      .then(result => dispatch(updateOauthBotUri(result.oauthUri)))
};

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
