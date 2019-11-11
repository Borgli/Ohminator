const initialState = {
    username: '',
    email: '',
    id: '',
    avatar: '',
    discriminator: '',
    locale: '',
    mfa_enabled: undefined,
    verified: undefined,
    flags: undefined
}

const user = (state = initialState, action) => {
    switch (action.type) {
        case "SET_USER_SUCCESS": {
            return {
                ...state,
                ...action.user
            }
        }
        case 'LOGOUT':
            return initialState;
        default:
            return state;
    }
};

export const getUsername = state => state.user.username;
export const getEmail = state => state.user.email;
export const getId = state => state.user.id;
export const getDiscriminator = state => state.user.discriminator;
export const getLocale = state => state.user.locale;
export const getAvatar = state => state.user.avatar;

export default user;

