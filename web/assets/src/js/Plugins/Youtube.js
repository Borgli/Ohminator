import React from "react";
import SaveChanges from "../SaveChanges";
import {connect} from "react-redux";
import DisableButton from "./Components/DisableButton";


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
        <DisableButton discord={this.props.discord}/>
        <SaveChanges/>
      </div>
    );
  }
}

let mapStateToProps = (state) => {
  return {discord: state.guildDashboard.discord}
};

export default connect(mapStateToProps)(Youtube);