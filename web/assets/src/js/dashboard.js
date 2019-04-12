import React from "react";
import NavBar from "./NavBar";
import ServerSelection from "./ServerSelection";
import GuildDashboard from "./GuildDashboard";
import Intro from "./Plugins/Intro";

let AUTH_URL = "https://discordapp.com/api/oauth2/authorize?client_id=315654415946219532&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Flogin&response_type=code&scope=identify%20email%20guilds";
let DASHBOARD_URL = "http://127.0.0.1:8000/dashboard";
let URLS = {
  authUrl: AUTH_URL,
  dashboardUrl: DASHBOARD_URL
};


let LandingPage = (props) => {
  return (
      <div className="container is-fluid">
        <div className="tile is-ancestor is-vertical">
          <div className="tile is-child box is-shadowless is-12">
            <div className="container has-text-centered">
              <h1 className="title">Ohminator</h1>
              <h1 className="title">The best bot ever</h1>
            </div>
          </div>
          <div className="tile is-child box is-12 is-shadowless has-text-centered">
            <a className="button is-primary" href={discord ? DASHBOARD_URL : AUTH_URL}>
              <strong>Add to Discord</strong>
            </a>
          </div>
        </div>
      </div>
  )
};


let PLUGINS = {
  'ohminator_web.introplugin': <Intro/>
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
            <LandingPage/>
          </div>
      )
    }
    // Plugin Dashboard
    else if (discord.plugin) {
      return PLUGINS[discord.plugin.model]
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
            <LandingPage/>
          </div>
      )
    }
  }
}

export default Dashboard;
