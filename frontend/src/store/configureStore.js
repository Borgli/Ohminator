import {applyMiddleware, compose, createStore} from "redux";
import { persistStore, persistReducer } from 'redux-persist'
import createSagaMiddleware from 'redux-saga'

import storage from 'redux-persist/lib/storage' // defaults to localStorage for web
import rootSaga from "../sagas";
import rootReducer from '../reducers';

const persistConfig = {
    key: 'root',
    storage
}

const persistedReducer = persistReducer(persistConfig, rootReducer)
const middlewares = [];
const enhancers = [];

const sagaMiddleware = createSagaMiddleware()
middlewares.push(sagaMiddleware)

// Needed for Redux Devtools plugin support
const reduxDevTools = window.__REDUX_DEVTOOLS_EXTENSION__ ? window.__REDUX_DEVTOOLS_EXTENSION__() : f => f

enhancers.push(applyMiddleware(...middlewares))
enhancers.push(reduxDevTools)

export const store = createStore(
    persistedReducer,
    compose(...enhancers)
)

sagaMiddleware.run(rootSaga)

export const persistor = persistStore(store)

