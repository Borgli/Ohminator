import React from 'react';
import {connect} from "react-redux";
import {
    useLocation,
    Redirect, Route
} from "react-router-dom";

const UserOauthHandler = ({path, setOauthCode, fetchUser}) => {
    // Browser specific. No IE11 support
    const query = new URLSearchParams(useLocation().search);
    setOauthCode(query.get('code'));
    fetchUser();

    return (
        <Route
            render={props => <Redirect {...props} to={{pathname: path, state: {from: props.location}}}/>}
        />
    );
}

const mapDispatchToProps = (dispatch) => ({
    setOauthCode: oauthCode => dispatch({type: 'SET_OAUTH_CODE', oauthCode}),
    fetchUser: () => dispatch({type: 'FETCH_USER'})
});

export default connect(null, mapDispatchToProps)(UserOauthHandler);