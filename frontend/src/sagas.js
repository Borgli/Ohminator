import { put, select, all, fork, takeEvery } from 'redux-saga/effects'
import { REHYDRATE } from 'redux-persist/lib/constants';
import {getOauthCode} from "./reducers/client";
import {fetchGuilds, fetchUser} from "./utils/calls";

function* getUserData() {
    const oauthCode = yield select(getOauthCode);
    if(oauthCode)
        yield fetchUser(oauthCode)
}

function* getGuilds() {
    const oauthCode = yield select(getOauthCode);
    if(oauthCode)
        yield fetchGuilds(oauthCode)
}


export default function* rootSaga() {
    yield all([
        yield takeEvery(REHYDRATE, getUserData),
        yield takeEvery('FETCH_GUILDS', getGuilds)
    ])
}