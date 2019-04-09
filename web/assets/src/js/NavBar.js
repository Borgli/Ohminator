import React from "react";


class NavBar extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <nav className="navbar" role="navigation" aria-label="main navigation">
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
                  <a className="navbar-item" href={"http://www.ohminator.com"}target="_blank">
                    Documentation
                  </a>
                </div>

                <div className="navbar-end">
                  <div className="navbar-item">
                    <div className="buttons">
                      <div className="navbar-item has-dropdown is-hoverable">
                    <a className="navbar-link">
                      Name
                    </a>

                    <div className="navbar-dropdown">
                      <a className="navbar-item">
                        Servers
                      </a>
                      <a className="navbar-item">
                        Logout
                      </a>
                      <hr className="navbar-divider"/>
                    </div>
                  </div>

                  <a className="button is-light">
                    Log in
                  </a>

                    </div>
                  </div>
                </div>
              </div>
            </nav>
        );
    }
}

export default NavBar;
