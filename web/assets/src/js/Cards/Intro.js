import React from "react";
import Default from "./Default";


class Intro extends React.Component {
    constructor(props) {
        super(props);

    }

    render() {
        return (
            <div>
                <Default title="Intros"/>
                <div className="tile is-4 is-vertical">

                </div>
            </div>
        );
    }
}

export default Intro;