import React, {useEffect} from 'react';
import {connect} from "react-redux";
import {
    useLocation,
    Redirect, Route
} from "react-router-dom";
import {getUser} from "../../utils/calls";

const Callback = ({path, setOauthCode}) => {

    // Browser specific. No IE11 support
    const query = new URLSearchParams(useLocation().search);
    setOauthCode(query.get('code'));
    console.log(query.get('code'));
    console.log(getUser(query.get('code')));

    return (
        <Route
            render={props => <Redirect {...props} to={{ pathname: path, state: { from: props.location }}}/>}
        />
        )
}

const mapDispatchToProps = (dispatch) => {
    return {
        setOauthCode: oauthCode => dispatch({type: 'SET_OAUTH_CODE', oauthCode})
    }
}

export default connect(null, mapDispatchToProps) (Callback);