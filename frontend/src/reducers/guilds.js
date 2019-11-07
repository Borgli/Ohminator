import guild from "./guild";

const initialState = {
    guilds: [],
};

const guilds = (state = initialState, action) => {
    switch(action.type) {
        case "ADD_GUILD":
            return {
                ...state,
                guilds: state.guilds.append(guild(state, action.guild))
            }
        default: return state;
    }
};

export const getGuilds = state => state.guilds.guilds;

export default guilds;