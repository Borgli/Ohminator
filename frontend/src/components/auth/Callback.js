import React from 'react';
import {connect} from "react-redux";
import {
    useLocation,
    Redirect, Route
} from "react-router-dom";
import {fetchUser} from "../../utils/calls";


const Callback = ({path, setOauthCode, setUser}) => {

    // Browser specific. No IE11 support
    const query = new URLSearchParams(useLocation().search);
    setOauthCode(query.get('code'));
    setUser(fetchUser(query.get('code')));


    return (
        <Route
            render={props => <Redirect {...props} to={{ pathname: path, state: { from: props.location }}}/>}
        />
        )
}

const mapDispatchToProps = (dispatch) => {
    return {
        setOauthCode: oauthCode => dispatch({type: 'SET_OAUTH_CODE', oauthCode}),
        setUser: user => dispatch({type: 'SET_USER', user})
    }
}

export default connect(null, mapDispatchToProps) (Callback);