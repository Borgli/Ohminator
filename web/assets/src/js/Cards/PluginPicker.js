import React from "react";
import PluginCard from "./PluginCard";

class PluginPicker extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className="tile is-parent box is-vertical is-12 has-background-grey-darker">
        <div className="tile is-child">
          <div className="title has-text-centered has-text-light">
            Plugins
          </div>
        </div>
        <div className="tile is-parent is-12">
          {this.props.discord.plugins.map((plugin, id) => {
            {
              return (
                <div key={id} className="tile is-child box has-text-centered has-background-grey-dark">
                  <PluginCard plugin={{title: plugin['fields'].name,
                    url_ending: plugin['fields'].url_ending,
                    isEnabled: plugin['fields'].enabled,
                    model: plugin.model}}/>
                </div>);
            }
          })}
        </div>
      </div>
    );
  }
}

export default PluginPicker;
