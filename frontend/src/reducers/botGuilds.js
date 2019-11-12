import botGuild from "./botGuild";
import {getCurrentGuild} from "./client";
import {LOGOUT, SET_BOT_GUILDS_SUCCESS} from "./actions";

const initialState = {
    guilds: [],
};

const botGuilds = (state = initialState, action) => {
    switch (action.type) {
        case SET_BOT_GUILDS_SUCCESS:
            return {
                ...state,
                guilds: action.guilds.map(currentGuild => botGuild(state.guilds, {type: 'SET_GUILD', guild: currentGuild}))
            };
        case LOGOUT:
            return initialState;
        default:
            return state;
    }
};

export const getBotGuilds = state => state.botGuilds.guilds;
export const getCurrentBotGuild = state => {
    const currentGuildId = getCurrentGuild(state)
    return state.botGuilds.guilds.find(guild => guild.id === currentGuildId)
}

export default botGuilds;