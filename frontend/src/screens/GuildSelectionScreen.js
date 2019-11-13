import React, {useEffect} from "react";
import {connect} from "react-redux";
import {getUsername} from "../reducers/user";
import {Link} from "react-router-dom";
import {getOauthGuildUri} from "../utils/utils";
import {getDiscordGuilds} from "../reducers/discordGuilds";
import {getBotGuilds} from "../reducers/botGuilds";
import {SET_CURRENT_GUILD} from "../reducers/actions";

const GUILD_PERMISSIONS_NEEDED = 2147483647;

const GuildSelectionScreen = ({username, discordGuilds, botGuilds}) => {

    return (
        <div id="guild-selection-screen">
            <section className="section">
                <div className="container is-fluid has-text-centered">
                    <p id="title" className="title is-1">
                        Welcome {username}!
                    </p>
                    <p className="subtitle is-4">
                        Select a guild
                    </p>
                </div>
            </section>
            <section id="guilds" className="section">
                <div className="columns is-multiline is-mobile is-centered">
                    {discordGuilds.map((guild, i) => {
                        if (guild.permissions === GUILD_PERMISSIONS_NEEDED)
                            return <GuildIcon
                                id={guild.id}
                                name={guild.name}
                                icon={guild.icon}
                                key={i}
                                botGuilds={botGuilds}
                            />
                    })}
                </div>
            </section>
        </div>
    );
};

const GuildIcon = ({id, name, icon, botGuilds}) => {
    return (
        <div className="column guild is-flex is-one-third has-text-centered">
            {botGuilds.some(guild => guild.id === id) ?
                <Link to={`/guilds/${id}`}>
                    <figure className="image is-128x128">
                        <img className="is-rounded"
                             src={`https://cdn.discordapp.com/icons/${id}/${icon}.png`}
                             alt='Avatar icon'
                        />
                    </figure>
                </Link>
                :
                <a href={getOauthGuildUri(id)}>
                    <figure className="image is-128x128">
                        <img className="is-rounded"
                             src={`https://cdn.discordapp.com/icons/${id}/${icon}.png`}
                             alt='Avatar icon'
                        />
                    </figure>
                </a>
            }
            <p className="is-size6 has-text-weight-bold">
                {name}
            </p>
        </div>
    )
};

const mapStateToProps = state => ({
    username: getUsername(state),
    discordGuilds: getDiscordGuilds(state),
    botGuilds: getBotGuilds(state),
});

export default connect(mapStateToProps)(GuildSelectionScreen);
