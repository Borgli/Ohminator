import botGuild from "./botGuild";

const initialState = {
    guilds: []
};

const botGuilds = (state = initialState, action) => {
    switch(action.type) {
        case "SET_BOT_GUILD_SUCCESS":
            return {
                ...state,
                guilds: botGuild(state.guilds, { type: 'SET_GUILD', guild: action.guild})
            };
        case 'LOGOUT':
            return initialState;
        default:
            return state;
    }
};

export const getBotGuilds = state => state.botGuilds.guilds;

export default botGuilds;