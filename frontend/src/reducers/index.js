import React from "react";
import {combineReducers} from "redux";
import client from "./client";
import guilds from "./guilds";
import user from "./user";

export default combineReducers({
    guilds,
    client,
    user
});

