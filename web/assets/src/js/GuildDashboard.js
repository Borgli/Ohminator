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
                    <div className="tile is-ancestor">
                        <div className="tile is-parent">

                            <div className="tile">
                                <GeneralSettings/>
                            </div>

                            <div className="tile">
                                <Youtube/>
                            </div>

                            <div className="tile">
                                <Intro/>
                            </div>

                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

export default GuildDashboard;
