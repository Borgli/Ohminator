import React from "react";
import NavBar from "./NavBar";
import ServerSelection from "./ServerSelection";
import GuildDashboard from "./GuildDashboard";

class Dashboard extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div>
                <NavBar/>
                {discord ?
                    discord.selected_guild ?
                        <GuildDashboard/>
                        :
                        <ServerSelection/>

                :
                    <div><a className="button"
                       href="https://discordapp.com/api/oauth2/authorize?client_id=315654415946219532&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Foauth_success&response_type=code&scope=identify%20guilds%20email%20connections">Press
                        me</a></div>
                }
            </div>
        );
    }
}

export default Dashboard;
