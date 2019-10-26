import {createStore} from "redux";
import rootReducer from '../reducers';

export default (initialState) => {
    const store = createStore(rootReducer, initialState);
    //For future
    return store;
}