import React from "react";
import NavBar from "./NavBar";
import ServerSelection from "./ServerSelection";

class Dashboard extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div>
                <NavBar/>
                <ServerSelection/>
            </div>
        );
    }
}

export default Dashboard;
