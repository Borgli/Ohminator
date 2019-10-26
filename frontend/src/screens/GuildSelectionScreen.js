import React from "react";

const GUILD_PERMISSIONS_NEEDED = 2147483647;
const SERVER_SELECTED_URL = "http://127.0.0.1:8000/api/guild/";

const GuildSelectionScreen = ({discord}) => {
    return (
        <div id="guild-selection-screen">
            <section className="section">
                <div className="container is-fluid has-text-centered">
                    <p id="title" className="title is-1">
                        Welcome {discord.user.username}!
                    </p>
                    <p className="subtitle is-4">
                        Select a server
                    </p>
                </div>
            </section>
            <section id="guilds" className="section">
                <div className="columns is-multiline is-mobile is-centered">
                    {discord.guilds.map( (guild, i) => {
                        if (guild.permissions === GUILD_PERMISSIONS_NEEDED) {
                            return (
                                <div className="column guild is-flex is-one-third has-text-centered" key={i}>
                                    <a href={SERVER_SELECTED_URL + guild.id}>
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

export default GuildSelectionScreen;
