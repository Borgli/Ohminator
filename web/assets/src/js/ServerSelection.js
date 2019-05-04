import React from "react";

let CLIENT_ID = "315654415946219532";
let REDIRECT_URL = "http://127.0.0.1:8000/api/bot_joined";
let SERVER_SELECTED_URL = "http://127.0.0.1:8000/api/guild/";

class ServerSelection extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div>
        <div className="tile is-ancestor is-vertical">
          <div className="tile is-parent">
            <div className="container has-text-centered box is-shadowless">
              <h1 className="title">Welcome {window.discord.user.username}!</h1>
              <h1 className="title">Select a server</h1>
            </div>
          </div>
          <div className="tile is-parent">
            {window.discord.guilds.map((guild) => {
              if (guild.permissions === 2146959359) {
                return (
                  <div className="tile box is-shadowless is-child">
                    <a href={SERVER_SELECTED_URL + guild.id}>
                      <figure className="image is-128x128">
                        <img className="is-rounded" src={"https://cdn.discordapp.com/icons/" + guild.id + "/" + guild.icon + ".png"}/>
                      </figure>
                    </a>
                  </div>);
              }
            })}
          </div>
        </div>
      </div>
    );
  }
}

export default ServerSelection;
