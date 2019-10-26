
const initialState = {
    prefix: '!',
    plugins: [],
};

const guild = (state = initialState, action) => {
    switch(action.type){
        case 'SET_GUILD_PREFIX':
            return {
                ...state,
                prefix: action.prefix
            };
        default:
            return state;
    }
};

export default guild;