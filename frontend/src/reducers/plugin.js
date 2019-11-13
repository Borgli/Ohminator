import {DISABLE_PLUGIN, ENABLE_PLUGIN} from "./actions";

const initialState = {
    name: '',
    active: false,
    features: {},
};

const plugin = (state = initialState, action) => {
    switch (action.type) {
        case ENABLE_PLUGIN:
            return {
                ...state,
                active: true
            }
        case DISABLE_PLUGIN:
            return {
                ...state,
                active: false
            }
        default:
            return state;
    }
}