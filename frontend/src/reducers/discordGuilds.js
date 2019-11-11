import discordGuild from "./discordGuild";

const initialState = {
    guilds: [],
};

const discordGuilds = (state = initialState, action) => {
    switch(action.type) {
        case "SET_DISCORD_GUILDS_SUCCESS":
            return {
                ...state,
                guilds: action.guilds.map(currentGuild => discordGuild(state.guilds, { type: 'SET_GUILD', guild: currentGuild}))
            };
        case 'LOGOUT':
            return initialState;
        default:
            return state;
    }
};

export const getDiscordGuilds = state => state.discordGuilds.guilds;

export default discordGuilds;