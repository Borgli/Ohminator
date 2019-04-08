import React from "react";
import PluginCard from "./PluginCard";


class GuildDashboard extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div>
                <PluginCard/>
            </div>
        );
    }
}

export default GuildDashboard;
