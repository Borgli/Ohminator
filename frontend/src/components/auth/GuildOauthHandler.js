import React from 'react';
import {connect} from "react-redux";
import {
    useLocation,
    Redirect,
    Route
} from "react-router-dom";

const GuildOauthHandler = ({registerGuild, setCurrentGuild, fetchUser}) => {
    const query = new URLSearchParams(useLocation().search);
    const id = query.get('guild_id')
    registerGuild(id)
    setCurrentGuild(id)
    const path = `/guilds/${id}`


    return (
        <Route
            render={props => <Redirect {...props} to={{pathname: path, state: {from: props.location}}}/>}
        />
    );
}

const mapDispatchToProps = (dispatch) => ({
    registerGuild: (id) => dispatch({type: 'REGISTER_GUILD', id}),
    setCurrentGuild: (id) => dispatch({type: 'SET_CURRENT_GUILD', id}),
    fetchUser: () => dispatch({type: "FETCH_USER"})
});

export default connect(null, mapDispatchToProps)(GuildOauthHandler);