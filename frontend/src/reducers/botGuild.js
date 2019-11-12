import {SET_GUILD, SET_GUILD_PREFIX} from "./actions";

const initialState = {
    id: '',
    prefix: '!',
    plugins: []

};

const botGuild = (state = initialState, action) => {
    switch (action.type) {
        case SET_GUILD:
            const id = action.guild.pk
            const fields = action.guild.fields
            return {
                ...state,
                id,
                ...fields
            };
        case SET_GUILD_PREFIX:
            return {
                ...state,
                prefix: action.prefix
            };
        default:
            return state;
    }
};

export default botGuild