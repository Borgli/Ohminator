import React from "react";

class Default extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      communication: "DM",
      enabled: false
    }

  }


  render() {
    return (
      <div>
        <div className="tile is-vertical">
          <div className="title">
            {this.props.title}
          </div>
          <form>
            <label className="checkbox">
              Enabled
              <input type="checkbox" onClick={() => {this.setState({enabled: !this.state.enabled}); console.log(this.state.enabled)}}/>
            </label>

            <div className="label">
              Communication:
            </div>
            <select>
              <option selected value="DM">Direct Message</option>
              <option value="CH">Specific Channel</option>
              <option value="U">User Channel</option>
              <option value="M">Muted</option>
            </select>
          </form>
        </div>
      </div>
    );
  }
}

export default Default;