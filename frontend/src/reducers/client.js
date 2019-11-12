import {LOGOUT, SET_CURRENT_GUILD, SET_OAUTH_CODE} from "./actions";

const initialState = {
    oauthCode: '',
    currentGuild: undefined
}

const client = (state = initialState, action ) => {
    switch(action.type){
        case SET_OAUTH_CODE:
            return {
                ...state,
                oauthCode: action.oauthCode
            }
        case SET_CURRENT_GUILD:
            return {
                ...state,
                currentGuild: action.id
            }
        case LOGOUT:
            return initialState;
        default:
            return state;
    }
}

export const getOauthCode = (state) => state.client.oauthCode;
export const getCurrentGuild = (state) => state.client.currentGuild

export default client;