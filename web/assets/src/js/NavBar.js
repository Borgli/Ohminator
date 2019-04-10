import React from "react";

let LOGOUT_URL = "http://127.0.0.1:8000/api/logout";

class NavBar extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <nav className="navbar is-primary" role="navigation" aria-label="main navigation">
        <div className="navbar-brand">
          <a className="navbar-item" href="/">
            <img src="https://image.flaticon.com/icons/svg/511/511139.svg" width="28" height="28"/>
            <p className={"has-text-weight-bold"} style={{marginLeft: '6px'}}>Ohminator</p>
          </a>

          <a role="button" className="navbar-burger burger" aria-label="menu" aria-expanded="false"
             data-target="navbarBasicExample">
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
            <span aria-hidden="true"></span>
          </a>
        </div>

        <div id="navbarBasicExample" className="navbar-menu">
          <div className="navbar-start">
            <a className="navbar-item" href={"http://www.ohminator.com"} target="_blank">
              Documentation
            </a>
          </div>

          <div className="navbar-end">
            <div className="navbar-item">
              <div className="buttons">
                <div className="navbar-brand">
                  <div className="navbar-item has-dropdown is-hoverable">
                    {this.props.login ?
                      <a className="navbar-link">
                        <img src={"https://cdn.discordapp.com/avatars/" +
                        this.props.login.id + "/" + this.props.login.avatar + ".png"}/>
                        {this.props.login.username}
                      </a>
                      :
                      <a className="navbar-link">Log in</a>
                    }


                    <div className="navbar-dropdown is-boxed">
                      <a className="navbar-item" href={this.props.login ? this.props.urls.dashboardUrl : this.props.urls.authUrl}>
                        Servers
                      </a>
                      <a className="navbar-item" href={LOGOUT_URL}>
                        Logout
                      </a>
                      <hr className="navbar-divider"/>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>
    );
  }
}

export default NavBar;
