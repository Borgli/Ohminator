import React from 'react';
import {connect} from "react-redux";
import {
    useLocation,
    Redirect,
    Route
} from "react-router-dom";

const GuildOauthHandler = ({registerGuild}) => {
    const query = new URLSearchParams(useLocation().search);
    console.log(query.get('guild_id'))
    registerGuild(query.get('guild_id'))

    const path = `/guilds/${query.get('guild_id')}`


    // return (
    //     <Route
    //         render={props => <Redirect {...props} to={{pathname: path, state: {from: props.location}}}/>}
    //     />
    // );

    return ( <div/> )
}

const mapDispatchToProps = (dispatch) => ({
    registerGuild: (id) => dispatch({type: 'REGISTER_GUILD', id})
});

export default connect(null, mapDispatchToProps)(GuildOauthHandler);