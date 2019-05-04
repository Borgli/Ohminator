import React from "react";
import GeneralSettings from "./Cards/GeneralSettings";
import PluginCard from "./Cards/PluginCard";
import { useSelector, connect } from 'react-redux';
import PluginPicker from "./Cards/PluginPicker";
import {updateDiscord} from "./actions";

class GuildDashboard extends React.Component {
  constructor(props) {
    super(props);
    //this.discord = useSelector(state => state.discord);
  }

  componentDidUpdate = (prevProps, prevState, snapshot) => {
    if (!this.props.discord.plugins) {
      fetch("http://127.0.0.1:8000/api/guild/" + this.props.discord.selected_guild.id + "/plugins")
        .then(response => response.json())
        .then(myJson => {console.log(myJson); this.props.dispatch(updateDiscord(myJson))});
    }
  };

  render() {
    console.log("GUILD_DASHBOARD: ", this.props);
    return (
      <div>
        <div className="container is-fluid">
          <div className="tile is-ancestor is-vertical">
            {this.props.discord.plugins ?
              this.props.displayPage ?
                this.props.displayPage
                :
                <div>
                  <div className="tile is-parent is-12">
                    <div className="container has-text-centered">
                      <h1 className="title">Current server:</h1>
                      <h1 className="title has-text-primary">{this.props.discord.selected_guild.name}</h1>
                    </div>
                  </div>

                  <div className="tile is-child box is-shadowless has-text-centered has-background-grey-darker">
                    <GeneralSettings/>
                  </div>
                  <PluginPicker discord={this.props.discord}/>
                </div>
              :
              "Loading..."
            }
          </div>
        </div>
      </div>
    );
  }
}

let mapStateToProps = (state) => {
  console.log(state);
  return {discord: state.guildDashboard.discord, displayPage: state.guildDashboard.displayPage}
};

export default connect(mapStateToProps)(GuildDashboard);
