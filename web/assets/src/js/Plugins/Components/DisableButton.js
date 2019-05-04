import React from "react";
import postData from "../../Utils/PostData";
import {connect} from "react-redux";
import {pluginDisabled, updatePluginPage} from "../../actions";



const DisableButton = (props) => {
  const link = "http://127.0.0.1:8000/dashboard/" + props.discord.selected_guild.id + "/plugin_status/" + props.discord.plugin['fields'].url_ending;
  return (<div className="tile is-parent is-12">
    <div className="tile is-child has-text-centered">
      <a onClick={(e) => {
        e.preventDefault();
        postData(link, {'enable_plugin': false})
          .then((myJson) => {
            props.dispatch(pluginDisabled())
          })
      }} className="button is-primary is-large is-centered"
         href={link}>Disable</a>
    </div>
  </div>);
};

export default connect()(DisableButton);
