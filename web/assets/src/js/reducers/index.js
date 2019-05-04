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
                discord: {...state.discord, ...action.discord},
                displayPage: action.plugin ? PLUGINS[action.plugin](action.pluginState) : undefined
            });
        case 'UPDATE_DISCORD':
            console.log('UPDATE_DISCORD: ', {...state.discord, ...action.discord});
            return Object.assign({}, state, {discord: {...state.discord, ...action.discord}});
        case 'PLUGIN_DISABLED':
            return Object.assign({}, state, {displayPage: undefined, discord: {...state.discord, plugins: undefined}});
    }
    return state;
};

export {guildDashboard};
