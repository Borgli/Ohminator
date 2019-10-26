import React from "react";


class SaveChanges extends React.Component {
  constructor(props) {
    super(props);
  }


  render() {
    return (
        <div className="tile is-parent is-12">
          <div className="tile is-child has-text-centered">
            <a className="button is-primary is-large is-centered">Save changes</a>
          </div>
        </div>
    );
  }
}

export default SaveChanges;
