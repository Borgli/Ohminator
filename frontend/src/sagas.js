import { put, select, all, fork, takeEvery } from 'redux-saga/effects'
import { REHYDRATE } from 'redux-persist/lib/constants';
import {getOauthCode} from "./reducers/client";
import {fetchUser} from "./utils/calls";

function* getUserData() {
    const oauthCode = yield select(getOauthCode)
    if(oauthCode)
        yield fetchUser(oauthCode)
}


export default function* rootSaga() {
    yield all([
        yield takeEvery(REHYDRATE, getUserData)
    ])
}