import React from "react";
import SaveChanges from "../SaveChanges";


class Intro extends React.Component {
    constructor(props) {
        super(props);

    }

    render() {
        return (
            <div>
                Halla bakka
                <SaveChanges/>
            </div>
        );
    }
}

export default Intro;