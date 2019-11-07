const initialState = {
    oauthCode: ''
}

const client = (state = initialState, action ) => {
    switch(action.type){
        case 'SET_OAUTH_CODE':
            return {
                ...state,
                oauthCode: action.oauthCode
            }
        default:
            return state;
    }
}

export const getOauthCode = (state) => {
    return state.client.oauthCode;
}

export default client;