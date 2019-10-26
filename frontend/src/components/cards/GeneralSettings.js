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
          {"General Settings"}
        </div>
        <div className="tile is-vertical">
          <form>
            <div className="label has-text-light">
              Prefix:
              <input type="text" placeholder="!"/>
            </div>
          </form>
        </div>
      </div>
    );
  }
}

export default GeneralSettings;