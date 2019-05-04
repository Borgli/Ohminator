import React from "react";
import NavBar from "./NavBar";
import ServerSelection from "./ServerSelection";
import GuildDashboard from "./GuildDashboard";
import Intro from "./Plugins/Intro";
import LandingPage from "./LandingPage";
import Youtube from "./Plugins/Youtube";

let AUTH_URL = "https://discordapp.com/api/oauth2/authorize?client_id=315654415946219532&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Flogin&response_type=code&scope=identify%20email%20guilds";
let DASHBOARD_URL = "http://127.0.0.1:8000/dashboard";
let URLS = {
  authUrl: AUTH_URL,
  dashboardUrl: DASHBOARD_URL
};


class Dashboard extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    // Not logged in
    if (!discord) {
      return (
        <div>
          <NavBar urls={URLS}/>
          <LandingPage urls={URLS}/>
        </div>
      )
    }
    // Server Select
    else if (discord.guilds && !discord.selected_guild) {
      return (
        <div>
          <NavBar login={discord.user} urls={URLS}/>
          <ServerSelection/>
        </div>
      )
    }
    // Guild Dashboard
    else if (!discord.guilds && discord.selected_guild) {
      return (
        <div>
          <NavBar login={discord.user} urls={URLS}/>
          <GuildDashboard/>
        </div>
      )
    }
    // Landing Page with login
    else {
      return (
        <div>
          <NavBar login={discord.user} urls={URLS}/>
          <LandingPage urls={URLS}/>
        </div>
      )
    }
  }
}

export default Dashboard;
