
const initialState = {
    prefix: '!',
    plugins: [],
    id: '',
    permissions: '',
    name: '',
    icon: ''
};

const guild = (state = initialState, action) => {
    switch(action.type){
        case 'ADD_GUILD':
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

export default guild;