import {takeLeading, select, all, takeEvery} from 'redux-saga/effects'
import {REHYDRATE} from 'redux-persist/lib/constants';
import {getOauthCode} from "./reducers/client";
import {fetchGuilds, fetchUser, postGuild} from "./utils/calls";

function* getUser() {
    const oauthCode = yield select(getOauthCode);
    if (oauthCode)
        yield fetchUser(oauthCode)
}

function* getGuilds() {
    const oauthCode = yield select(getOauthCode);
    if (oauthCode)
        yield fetchGuilds(oauthCode)
}

function* registerGuild(action) {
    const oauthCode = yield select(getOauthCode);
    console.log(action)
    if (oauthCode)
        yield postGuild(action.id, oauthCode)

}


export default function* rootSaga() {
    yield all([
        yield takeLeading(REHYDRATE, getUser),
        yield takeEvery('FETCH_USER', getUser),
        yield takeEvery('SET_USER_SUCCESS', getGuilds),
        yield takeEvery('REGISTER_GUILD', registerGuild)
    ])
}