import React from "react";

class GeneralSettings extends React.Component {
  constructor(props) {
    super(props);

    this.communication = "DM"
  }

  render() {
    return (
      <div>
        <div className="title has-text-light">
          {this.props.title = "General Settings"}
        </div>
        <div className="tile is-vertical">
          <form>
            <div className="label has-text-light">
              Prefix:
              <input type="text" value="!"/>
            </div>
          </form>
        </div>
      </div>
    );
  }
}

export default GeneralSettings;