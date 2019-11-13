import React, {useState, useEffect} from "react";
import {connect} from 'react-redux';
import LoadingIcon from "../components/icons/LoadingIcon";
import PluginCard from "../components/cards/PluginCard";
import {getCurrentBotGuild} from "../reducers/botGuilds";
import {getCurrentDiscordGuild} from "../reducers/discordGuilds";
import {SET_CURRENT_GUILD} from "../reducers/actions";
import GeneralSettingsCard from "../components/cards/GeneralSettingsCard";


const GuildScreen = ({discordGuild, botGuild, setCurrentGuild, match}) => {
    useEffect(() => {
        setCurrentGuild(match.params.id)
        // TOD
        // if (!botGuild.plugins)
    }, []);

    // TODO Fix icon for guilds without avatar
    return (
        <div id="guild-screen">
            <section className="section">
                <div className="container guild is-fluid has-text-centered">
                    <figure className="image is-128x128 is-flex is-centered" >
                        <img className="is-rounded"
                             src={`https://cdn.discordapp.com/icons/${discordGuild.id}/${discordGuild.icon}.png`}/>
                    </figure>
                    <p className="title is-1">
                        {discordGuild.name}
                    </p>
                </div>
            </section>
            <GeneralSettingsCard
                prefix={botGuild.prefix}
            />
            <section id="plugins" className="section">
                <div className="title has-text-centered">
                    Plugins
                </div>
                <div className="columns is-multiline is-centered">
                    {
                       botGuild.plugins ?
                           botGuild.plugins.map((plugin, i) =>
                               <PluginCard key={i}/>
                           )
                           :
                           <LoadingIcon/>
                    }
                </div>
            </section>
        </div>
    );
};

const mapStateToProps = (state) => {
    return {
        botGuild: getCurrentBotGuild(state),
        discordGuild: getCurrentDiscordGuild(state)
    }
};

const mapDispatchToProps = dispatch => ({
    setCurrentGuild: (id) => dispatch({type: SET_CURRENT_GUILD, id})
})

export default connect(mapStateToProps, mapDispatchToProps)(GuildScreen);
