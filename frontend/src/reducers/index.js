import React from "react";
import {combineReducers} from "redux";
import client from "./client";
import user from "./user";
import discordGuilds from "./discordGuilds";
import botGuilds from "./botGuilds";

export default combineReducers({
    discordGuilds,
    botGuilds,
    client,
    user
});

