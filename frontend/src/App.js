import React from "react";
import {
    BrowserRouter as Router,
    Switch,
    Route,
    Redirect
} from "react-router-dom";
import {connect} from "react-redux";

import Navbar from "./components/navbar/Navbar";
import GuildSelectionScreen from "./screens/GuildSelectionScreen";
import LandingScreen from "./screens/LandingScreen";
import Footer from "./components/Footer";
import GuildOauthHandler from "./components/auth/GuildOauthHandler";
import UserOauthHandler from "./components/auth/UserOauthHandler";
import GuildScreen from "./screens/GuildScreen";

const AuthenticatedRoute = ({component: Component, oauthCode, ...rest}) => (
    <Route
        {...rest}
        render={props =>
            oauthCode ?
                <Component {...rest} {...props} />
                :
                <Redirect to={{pathname: "/login", state: {from: props.location}}}/>

        }
    />
)

const App = ({oauthCode}) => {
    return (
        <Router className='app'>
            <Navbar/>
            <Switch>
                <Route path='/guilds/:id'>
                    <AuthenticatedRoute
                        oauthCode={oauthCode}
                        path={'/guilds/:id'}
                        component={GuildScreen}
                    />
                </Route>
                <Route path='/guilds'>
                    <AuthenticatedRoute
                        oauthCode={oauthCode}
                        path={'/guilds'}
                        component={GuildSelectionScreen}
                    />
                </Route>
                <Route path='/auth/user/discord'>
                    <UserOauthHandler
                        path='/guilds'
                    />
                </Route>
                <Route path='/auth/guild/discord'>
                    <GuildOauthHandler
                        path='/guilds/:id'
                    />
                </Route>
                <Route path='/'>
                    <LandingScreen/>
                </Route>
            </Switch>
            <Footer/>
        </Router>
    );
};

const mapStateToProps = state => ({oauthCode: state.client.oauthCode})

export default connect(mapStateToProps)(App);
