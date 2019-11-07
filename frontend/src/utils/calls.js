import Cookies from "js-cookie";
import "regenerator-runtime/runtime";
import {put} from "redux-saga/effects";

const config = require('config');

export function* fetchUser(oauthCode) {
    yield fetchApi(oauthCode, (response) => ({type: 'SET_USER_SUCCESS', user: response.user}),
      (error) => ({type: 'SET_USER_FAILURE', error}), '/api/user');
}

export function* fetchGuilds(oauthCode) {
    yield fetchApi(oauthCode, (response) => ({type: 'SET_GUILDS_SUCCESS', guilds: response.guilds}),
      (error) => ({type: 'SET_GUILDS_FAILURE', error}), '/api/guilds');
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
