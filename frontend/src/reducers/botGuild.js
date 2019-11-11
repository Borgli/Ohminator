const initialState = {
    prefix: '!',
    plugins: []

};

const botGuild = (state = initialState, action) => {
    switch (action.type) {
        case 'SET_GUILD':
            return {
                ...state,
                ...action.guild
            };
        case 'SET_GUILD_PREFIX':
            return {
                ...state,
                prefix: action.prefix
            };
        default:
            return state;
    }
};

export default botGuild