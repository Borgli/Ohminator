import React, {useState, useEffect} from "react";
import {connect} from 'react-redux';
import {getGuildPlugins} from "../utils/calls";
import LoadingIcon from "../components/icons/LoadingIcon";
import PluginCard from "../components/cards/PluginCard";
import {getCurrentBotGuild} from "../reducers/botGuilds";
import {getCurrentDiscordGuild} from "../reducers/discordGuilds";


const GuildScreen = ({discordGuild, botGuild}) => {
    const [prefixTemp, setPrefixTemp] = useState(botGuild.prefix);
    useEffect(() => {
        if (!botGuild.plugins)
           console.log('eeh')

    });

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
            <section id="general-settings" className="section">
                <div className="card">
                    <header className="card-header">
                        <p className="card-header-title">
                            General settings
                        </p>
                    </header>
                    <div className="card-content">
                        <div className="content">
                            <div className="field">
                                <input className="input" type="text" placeholder={prefixTemp}/>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
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

export default connect(mapStateToProps)(GuildScreen);
