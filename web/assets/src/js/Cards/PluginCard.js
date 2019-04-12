import React from "react";

class PluginCard extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div>
        {this.props.plugin.isEnabled ?
          <div className="tile is-child box is-shadowless has-text-centered has-background-grey-dark">
            <a
              href={"http://127.0.0.1:8000/dashboard/" + window.discord.selected_guild.id + "/" + this.props.plugin.url_ending}>
              <div className="tile is-vertical has-background-grey-dark">
                <div className="title has-text-light">
                  {this.props.plugin.title}
                </div>
              </div>
            </a>
          </div>
          :
          <div className="tile is-child box is-shadowless has-text-centered has-background-grey-darker">
            <a
              href={"http://127.0.0.1:8000/dashboard/" + window.discord.selected_guild.id + "/enable/" + this.props.plugin.url_ending}>
              <div className="tile is-vertical has-background-grey-darker">
                <div className="title has-text-light">
                  {this.props.plugin.title}
                  {"(Disabled)"}
                </div>
              </div>
            </a>
          </div>
        }
      </div>
    );
  }
}

export default PluginCard;
