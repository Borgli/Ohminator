import React from "react";
import GuildDashboard from "../GuildDashboard";
import Youtube from "../Plugins/Youtube";
import Intro from "../Plugins/Intro";

let PLUGINS = {
  'ohminator_web.introplugin': (data) => <Intro data={data}/>,
  'ohminator_web.youtubeplugin': (data) => <Youtube data={data}/>
};

let guildDashboard = (state = {displayPage: undefined, discord: window.discord}, action) => {
    console.log("REDUCER: ", state, action);
    switch (action.type) {
        case 'UPDATE_PLUGIN_PAGE':
            console.log('UPDATE_PLUGIN_PAGE: ', action.plugin);
            return Object.assign({}, state, {
                discord: action.discord,
                displayPage: PLUGINS[action.plugin](action.pluginState)
            });
        case 'UPDATE_DISCORD':
            return Object.assign({}, state, {discord: action.discord});
    }
    return state;
};

export {guildDashboard};
