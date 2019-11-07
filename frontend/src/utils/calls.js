import Cookies from "js-cookie";
import "regenerator-runtime/runtime";
import {put} from "redux-saga/effects";

const config = require('config');

export function* fetchUser(oauthCode) {
    let headers = {'Content-Type': 'application/json'};
    headers['X-Oauth-Code'] = oauthCode;

    try {
        const response = yield fetch(config.endpoint + '/api/user', {headers})
            .then(response => response.json());

        yield put({type: 'SET_USER_SUCCESS', user: response.user})
    } catch (error) {
        yield put({type: 'SET_USER_FAILURE', error})
    }
}

export const fetchGuilds = (oauthCode) => {
    let headers = {'Content-Type': 'application/json'};
    headers['X-Oauth-Code'] = oauthCode;

    return fetch(config.endpoint + '/api/guilds', {headers})
        .then(response => response.json())
        .then(result => result);
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
