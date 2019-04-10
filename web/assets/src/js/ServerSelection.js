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
              {window.discord.user.username}, please select a server:
              <div className="columns">
                  <div className="column">
                      {window.discord.guilds.map((guild) => {
                          if (guild.permissions === 2146958847) {
                              return (
                                <a href={SERVER_SELECTED_URL + guild.id}>
                                    <figure className="image is-128x128">
                                        <img className="is-rounded" src={"https://cdn.discordapp.com/icons/" + guild.id + "/" + guild.icon + ".png"}/>
                                    </figure>
                                </a>);
                          }
                      })}
                  </div>
              </div>
          </div>
        );
    }
}

export default ServerSelection;
