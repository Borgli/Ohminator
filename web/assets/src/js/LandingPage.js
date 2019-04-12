import React from "react";



class LandingPage extends React.Component {
  constructor(props) {
    super(props);
  }


  render() {
    return (
      <div className="container is-fluid">
        <div className="tile is-ancestor is-vertical">
          <div className="tile is-child box is-shadowless is-12">
            <div className="container has-text-centered">
              <h1 className="title">Ohminator</h1>
              <h1 className="title">The best bot ever</h1>
            </div>
          </div>
          <div className="tile is-child box is-12 is-shadowless has-text-centered">
            <a className="button is-primary" href={discord ? this.props.urls.dashboardUrl : this.props.urls.authUrl}>
              <strong>Add to Discord</strong>
            </a>
          </div>
        </div>
      </div>
    );
  }
}

export default LandingPage;
