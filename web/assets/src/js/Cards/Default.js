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
        <div className="tile is-parent">
          <div className="tile is-4 is-vertical">
            {this.props.title}
            <form>
              <label className="checkbox">
                Enabled
                <input type="checkbox" onClick={() => {this.setState({enabled: !this.state.enabled}); console.log(this.state.enabled)}}/>
              </label>

              <label>
                Communication:
                <select>
                  <option selected value="DM">Direct Message</option>
                  <option value="CH">Specific Channel</option>
                  <option value="U">User Channel</option>
                  <option value="M">Muted</option>
                </select>
              </label>
            </form>
          </div>
        </div>
      </div>
    );
  }
}

export default Default;