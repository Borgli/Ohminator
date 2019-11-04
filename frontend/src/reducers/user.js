const initialState = {
    username: '',
    email: '',
    id: '',
    avatar: '',
    discriminator: '',
    locale: '',
}

const user = (state = initialState, action) => {
    switch (action.type) {
        case "SET_USER": {
            return {
                ...state,
                ...action.user
            }
        }
        default:
            return state;
    }
};

export const getUsername = state => state.username;
export const getEmail = state => state.email;
export const getId = state => state.id;
export const getDiscriminator = state => state.discriminator;
export const getLocale = state => state.locale;

export default user;

