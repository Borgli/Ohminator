const initialState = {
    id: '',
    permissions: '',
    name: '',
    owner: '',
    icon: '',
    features: [],

};

const discordGuild = (state = initialState, action) => {
    switch(action.type){
        case 'SET_GUILD':
            return {
                ...state,
                ...action.guild
            };
        default:
            return state;
    }
};

export default discordGuild;