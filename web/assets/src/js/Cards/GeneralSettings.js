import React from "react";

class GeneralSettings extends React.Component {
    constructor(props) {
        super(props);

        this.communication = "DM"
    }

    render() {
        return (
            <div>
                {this.props.title = "General Settings"}
                <div className="tile is-vertical">
                    <form>
                        <label>
                            Prefix:
                            <input type="text" value="!"/>
                        </label>
                    </form>
                </div>
            </div>
        );
    }
}

export default GeneralSettings;