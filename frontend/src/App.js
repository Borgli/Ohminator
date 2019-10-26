import React from "react";
import Navbar from "./components/navbar/Navbar";
import GuildSelectionScreen from "./screens/GuildSelectionScreen";
import GuildDashboard from "./screens/GuildScreen";
import LandingScreen from "./screens/LandingScreen";
import Footer from "./components/Footer";

const AUTH_URL = "https://discordapp.com/api/oauth2/authorize?client_id=315654415946219532&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Flogin&response_type=code&scope=identify%20email%20guilds";
const DASHBOARD_URL = "http://127.0.0.1:8000/dashboard";
const URLS = {
  authUrl: AUTH_URL,
  dashboardUrl: DASHBOARD_URL
};

// TODO Decide on routing
const getRoute = (discord) => {
    // Guild select
    if (discord && discord.guilds && !discord.selected_guild)
        return <GuildSelectionScreen discord={discord}/>;
    // Guild dashboard
    if (discord && !discord.guilds && discord.selected_guild)
        return <GuildDashboard/>;
    // Landing screen
    return <LandingScreen urls={URLS}/>
};

const App = () => {
    return (
        <div id="app" >
            <Navbar login={null} urls={URLS}/>
            { getRoute(null) }
            <Footer/>
        </div>

    );
};

export default App;
