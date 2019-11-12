import React, {useEffect, useState} from "react";

import "../styles/screens/_landingScreen.scss";
import {getOauthUserUri} from '../utils/utils';
import DiscordLogo from "../components/icons/DiscordLogo";
import {getOauthCode} from "../reducers/client";

import {connect} from "react-redux";
import {Link} from "react-router-dom";

const LandingScreen = ({oauthCode}) => {
    const oauthUri = getOauthUserUri()

    return (
        <div id="landing-screen">
            <div id="content">
                <section className="section">
                    <div className="container is-fluid has-text-centered">
                        <p id="title" className="title is-1">
                            Ω Ohminator
                        </p>
                        <p className="subtitle is-4">
                            The best bot ever
                        </p>
                    </div>
                </section>
                <section id="plugins" className="section">
                    <div className="columns is-multiline is-mobile is-centered ">
                        <div className="column is-one-third has-text-centered">
                            <p className="title">
                                Test text
                            </p>
                            <p className="subtitle">
                                Subtitle
                            </p>
                        </div>
                        <div className="column is-one-third has-text-centered">
                            <p className="title">
                                Test text
                            </p>
                            <p className="subtitle">
                                Subtitle
                            </p>
                        </div>
                        <div className="column is-one-third has-text-centered">
                            <p className="title">
                                Test text
                            </p>
                            <p className="subtitle">
                                Subtitle
                            </p>
                        </div>
                        <div className="column is-one-third has-text-centered">
                            <p className="title">
                                Test text
                            </p>
                            <p className="subtitle">
                                Subtitle
                            </p>
                        </div>
                        <div className="column is-one-third has-text-centered">
                            <p className="title">
                                Test text
                            </p>
                            <p className="subtitle">
                                Subtitle
                            </p>
                        </div>
                        <div className="column is-one-third has-text-centered">
                            <p className="title">
                                Test text
                            </p>
                            <p className="subtitle">
                                Subtitle
                            </p>
                        </div>
                    </div>
                </section>
                <section className="section">
                    <div className="container is-fluid has-text-centered">
                        {
                            oauthCode ?
                                <Link id="dashboard-button" className="button is-primary" to="/guilds">
                                    To dashboard
                                </Link>
                                :
                                <a id="discord-button" className="button is-primary"
                                   href={oauthUri}>
                                    Add to
                                    <DiscordLogo/>
                                </a>
                        }
                    </div>
                </section>
            </div>
        </div>
    );
};

const mapStateToProps = state => {
    return {
        oauthCode: getOauthCode(state),
    }
};

export default connect(mapStateToProps)(LandingScreen);
