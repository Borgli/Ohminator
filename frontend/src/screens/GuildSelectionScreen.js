import React, {useEffect} from "react";
import {getOauthCode} from "../reducers/client";
import {connect} from "react-redux";
import {getUsername} from "../reducers/user";
import {fetchGuilds} from "../utils/calls";
import {getGuilds} from "../reducers/guilds";

const GUILD_PERMISSIONS_NEEDED = 2147483647;

const GuildSelectionScreen = ({oauthCode, username, guilds}) => {
    useEffect(() => {
        // Fetch data here
        console.log(fetchGuilds(oauthCode))
    });

    console.log(guilds)

    return (
        <div id="guild-selection-screen">
            <section className="section">
                <div className="container is-fluid has-text-centered">
                    <p id="title" className="title is-1">
                        Welcome {username}!
                    </p>
                    <p className="subtitle is-4">
                        Select a server
                    </p>
                </div>
            </section>
            <section id="guilds" className="section">
                <div className="columns is-multiline is-mobile is-centered">
                    {guilds.map( (guild, i) => {
                        if (guild.permissions === GUILD_PERMISSIONS_NEEDED) {
                            return (
                                <div className="column guild is-flex is-one-third has-text-centered" key={i}>
                                    <a href={guild.id}>
                                        <figure className="image is-128x128" >
                                            <img className="is-rounded"
                                                 src={`https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`}/>
                                        </figure>
                                    </a>
                                    <p className="is-size6 has-text-weight-bold">
                                        {guild.name}
                                    </p>
                                </div>
                            );
                        }
                    })}
                </div>
            </section>
        </div>
    );
};

const mapStateToProps = state => {
    return {
        oauthCode: getOauthCode(state),
        username: getUsername(state),
        guilds: getGuilds(state)
    }
};

export default connect(mapStateToProps)(GuildSelectionScreen);
