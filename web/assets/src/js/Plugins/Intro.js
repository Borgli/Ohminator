import React from "react";
import SaveChanges from "../SaveChanges";


class Intro extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      communication: "DM",
    }
  }

  render() {
    return (
      <div>
        Halla bakka
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
               href={"http://127.0.0.1:8000/dashboard/" + window.discord.selected_guild.id + "/disable/" + window.discord.plugin['fields'].url_ending}>Disable</a>
          </div>
        </div>
        <SaveChanges/>
      </div>
    );
  }
}

export default Intro;