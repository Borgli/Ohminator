import React from "react";
import Cookies from 'js-cookie';
import { connect } from 'react-redux';
import {updatePluginPage, updateDiscord} from "../actions";

function postData(url = ``, data = {}) {
  // Default options are marked with *
    return fetch(url, {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        credentials: "same-origin", // include, *same-origin, omit
        headers: {
            "Content-Type": "application/json",
            'X-CSRFToken': Cookies.get("csrftoken"),
            'Accept': "application/json"
            // "Content-Type": "application/x-www-form-urlencoded",
        },
        body: JSON.stringify(data), // body data type must match "Content-Type" header
    })
    .then(response => {console.log(response); return response.json()}); // parses JSON response into native Javascript objects
}

class PluginCard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {pluginEnabled: this.props.plugin.isEnabled};
  }

  render() {
    console.log(this.props);
    let bgColour = this.state.pluginEnabled ? 'dark' : 'darker';
    let link = "http://127.0.0.1:8000/dashboard/" + this.props.discord.selected_guild.id + (this.state.pluginEnabled ? "/" : "/plugin_status/") + this.props.plugin.url_ending;
    let enablePlugin = (e) => {
        e.preventDefault();
        postData(link, {'enable_plugin': true})
            .then((myJson) => {console.log(myJson); this.setState({pluginEnabled: myJson.plugin_enabled})});
    };
    let getPluginInterface = (e) => {
        e.preventDefault();
        fetch(link, {}).then(response => response.json())
          .then((myJson) => {
            let myDiscord = JSON.parse(myJson.data.discord);
            this.props.dispatch(updatePluginPage(this.props.plugin.model, myDiscord));
          })
    };
    return (
        <div>
          <div className={"tile is-child box is-shadowless has-text-centered has-background-grey-" + bgColour} >
            <a onClick={this.state.pluginEnabled ? getPluginInterface : enablePlugin} href={link}>
              <div className={"tile is-vertical has-background-grey-" + bgColour}>
                <div className="title has-text-light">
                  {this.props.plugin.title}
                  {!this.state.pluginEnabled && "(Disabled)"}
                </div>
              </div>
            </a>
          </div>
        </div>
    );
  }
}

let mapStateToProps = (state) => {
  return {discord: state.guildDashboard.discord}
};


export default connect(mapStateToProps)(PluginCard);
