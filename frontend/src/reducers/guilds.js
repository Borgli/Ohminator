import guild from "./guild";

const initialState = {
    guilds: [],
};

const guilds = (state = initialState, action) => {
    switch(action.type) {
        case "SET_GUILDS_SUCCESS":
            return {
                ...state,
                guilds: action.guilds.map(currentGuild => guild(state.guilds, { type: 'ADD_GUILD', guild: currentGuild}))
            };
        default:
            return state;
    }
};

export const getGuilds = state => state.guilds.guilds;

export default guilds;