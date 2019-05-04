import React from "react";
import SaveChanges from "../SaveChanges";
import {connect} from "react-redux";


class Youtube extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      communication: "DM",
    }
  }

  render() {
    return (
      <div>
        Yo yo
        <form>
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
        <div className="tile is-parent is-12">
          <div className="tile is-child has-text-centered">
            <a className="button is-primary is-large is-centered"
               href={"http://127.0.0.1:8000/dashboard/" + this.props.discord.selected_guild.id + "/disable/" + this.props.discord.plugin['fields'].url_ending}>Disable</a>
          </div>
        </div>
        <SaveChanges/>
      </div>
    );
  }
}

let mapStateToProps = (state) => {
  return {discord: state.guildDashboard.discord}
};

export default connect(mapStateToProps)(Youtube);