import React from 'react';
import ReactDOM from 'react-dom';
import * as serviceWorker from './serviceWorker';
import App from "./App";
import './styles/_main.scss';
import {Provider} from "react-redux";
import { PersistGate } from 'redux-persist/integration/react'
import {persistor, store} from "./store/configureStore";
import firebase from "firebase/app";
import "firebase/analytics";
import "firebase/auth";
import "firebase/database";
import "firebase/storage";

// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyAlYwTVZ4z2AJ2uGECELWqROj8UHgcRX7k",
  authDomain: "ohminator-1337.firebaseapp.com",
  databaseURL: "https://ohminator-1337.firebaseio.com",
  projectId: "ohminator-1337",
  storageBucket: "ohminator-1337.appspot.com",
  messagingSenderId: "1010511411531",
  appId: "1:1010511411531:web:fc2aefd8a79a076f6810ce",
  measurementId: "G-2F5F4649PV"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

ReactDOM.render(
    <Provider store={store}>
        <PersistGate loading={null} persistor={persistor}>
            <App/>
        </PersistGate>
    </Provider>,

    document.getElementById('root'));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
