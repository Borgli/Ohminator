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
        <div className="tile is-vertical has-background-grey-dark">
          <div className="title has-text-light">
            <a href={"http://127.0.0.1:8000/dashboard/" + window.discord.selected_guild.id + "/" + this.props.plugin.url_ending}>
            {this.props.plugin.title}
            </a>
          </div>
          <form>
            <label className="checkbox has-text-light">
              Enabled
              <input type="checkbox" onClick={() => {this.setState({enabled: !this.state.enabled}); console.log(this.state.enabled)}}/>
            </label>

            <div className="label has-text-light">
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