import React from 'react';
import ReactDOM from 'react-dom';
import * as serviceWorker from './serviceWorker';
import Dashboard from "./dashboard";
import "../css/bulma.css";
import * as reducers from "./reducers";
import {Provider} from "react-redux";
import {combineReducers, createStore} from "redux";

const store = createStore(combineReducers(reducers));

ReactDOM.render(
    <Provider store={store}>
        <Dashboard/>
    </Provider>,
    document.getElementById('root'));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
