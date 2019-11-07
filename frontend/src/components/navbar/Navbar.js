import React from "react";

import '../../styles/components/_navbar.scss'
import {connect} from "react-redux";
import {getAvatar, getDiscriminator, getId, getUsername} from "../../reducers/user";

const LOGOUT_URL = "http://127.0.0.1:8000/api/logout";


const Navbar = ({username, avatar, discriminator, id, urls, transparent = true}) => {
    //TODO Refactor?
    const avatarSource = username ? avatar ?
        `https://cdn.discordapp.com/avatars/${id}/${avatar}.png`
        :
        `https://cdn.discordapp.com/embed/avatars/${discriminator % 5}.png`
        :
        null;

    return (
        <nav className="navbar" role="navigation" aria-label="main navigation">
            <div className="navbar-brand">
                <a className="navbar-item" href="/">
                    <p className="has-text-weight-bold" style={{marginLeft: '6px'}}>Ω Ohminator</p>
                </a>
                <a role="button" className="navbar-burger burger" aria-label="menu" aria-expanded="false"/>
            </div>
            <div className="navbar-menu">
                <div className="navbar-start">
                    <a className="navbar-item" href="http://www.ohminator.com">
                        Documentation
                    </a>
                </div>
                <div className="navbar-end">
                    <div className="navbar-item">
                        {id &&
                            <figure id="avatar" className="image is-48x48 is-flex">
                                <img className="is-rounded" src={avatarSource}/>
                            </figure>
                        }
                        {id ?
                            <div id="avatar-container" className="navbar-item is-hoverable has-dropdown">
                                <p className="is-size-5 has-text-weight-bold navbar-link">
                                    {username}
                                </p>
                                <div className="navbar-dropdown is-boxed">
                                    <a className="navbar-item"
                                       href={id ? '' : ''}>
                                        Servers
                                    </a>
                                    <hr className="navbar-divider"/>
                                    <a className="navbar-item" href={LOGOUT_URL}>
                                        Logout
                                    </a>
                                </div>
                            </div>
                            :
                            <a className="navbar-link">Log in</a>
                        }
                    </div>
                </div>
            </div>
        </nav>
    );
};

const mapStateToProps = state => ({
        username: getUsername(state),
        avatar: getAvatar(state),
        id: getId(state),
        discriminator: getDiscriminator(state)
})

export default connect(mapStateToProps)(Navbar);
