import discordGuild from "./discordGuild";
import {getCurrentGuild} from "./client";
import {LOGOUT, SET_DISCORD_GUILDS_SUCCESS} from "./actions";

const initialState = {
    guilds: [],
};

const discordGuilds = (state = initialState, action) => {
    switch(action.type) {
        case SET_DISCORD_GUILDS_SUCCESS:
            return {
                ...state,
                guilds: action.guilds.map(currentGuild => discordGuild(state.guilds, { type: 'SET_GUILD', guild: currentGuild}))
            };
        case LOGOUT:
            return initialState;
        default:
            return state;
    }
};

export const getDiscordGuilds = state => state.discordGuilds.guilds;
export const getCurrentDiscordGuild = state => {
    const currentGuildId = getCurrentGuild(state)
    return state.discordGuilds.guilds.find(guild => guild.id === currentGuildId)
}

export default discordGuilds;