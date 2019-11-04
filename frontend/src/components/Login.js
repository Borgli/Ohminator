import React from 'react';
import {Redirect, Route} from "react-router-dom";

export default ({component: Component, hasAuthCode, ...rest}) => (
    <Route
        {...rest}
        render={props =>
            hasAuthCode ?
                <Component {...rest} {...props} />
                :
                <Redirect to={{ pathname: "/login", state: { from: props.location }}} />

        }
    />
)
