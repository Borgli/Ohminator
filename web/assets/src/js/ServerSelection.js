import React from "react";

let CLIENT_ID = "315654415946219532";
let REDIRECT_URL = "http://127.0.0.1:8000/api/bot_joined";

class ServerSelection extends React.Component {
    constructor(props) {
        super(props);

    }

    render() {
        return (
            <div>
                {window.user.username} Please select a server.
                <div className="columns">
                    <div className="column">
                        {window.guilds.map((guild) => {
                            if (guild.permissions === 2146958847) {
                                return <a href={"https://discordapp.com/oauth2/authorize?scope=bot&response_type=code&redirect_uri=" + REDIRECT_URL + "&permissions=66321471&client_id=" + CLIENT_ID + "&guild_id=" + guild.id}>{guild.name}</a>
                            }
                        })}
                    </div>
                </div>
            </div>
        );
    }
}

export default ServerSelection;
