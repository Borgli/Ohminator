import React from "react";
import Youtube from "./Cards/Youtube";
import GeneralSettings from "./Cards/GeneralSettings";
import Intro from "./Cards/Intro";


class GuildDashboard extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
          <div>


              <div className="container is-fluid">
                  <div className="tile is-ancestor is-vertical has-background-grey-light">

                      <div className="tile is-parent is-12">
                          <div className="container has-text-centered">
                              <h1 className="title">Current server:</h1>
                              <h1 className="title has-text-primary">{window.discord.selected_guild.name}</h1>
                          </div>
                      </div>

                      <div className="tile is-parent is-12">
                          <div className="tile is-child box has-text-centered has-background-warning">
                              <GeneralSettings/>
                          </div>
                      </div>

                      <div className="tile is-parent is-vertical is-12 has-background-success">
                          <div className="tile is-child">
                              <div className="title has-text-centered">
                                  Plugins
                              </div>
                          </div>
                          <div className="tile is-parent is-12">
                              <div className="tile is-child box has-text-centered has-background-danger">
                                  <Youtube/>
                              </div>

                              <div className="tile is-child box has-text-centered has-background-info">
                                  <Intro/>
                              </div>
                          </div>
                      </div>

                      <div className="tile is-parent is-12">
                          <div className="tile is-child has-text-centered">
                              <a className="button is-primary is-large is-centered">Save changes</a>
                          </div>
                      </div>
                  </div>
              </div>>
          </div>
        );
    }
}

export default GuildDashboard;
