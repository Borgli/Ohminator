import React, {PropTypes} from "react";
import {
    BrowserRouter as Router,
    Switch,
    Route,
    Redirect
} from "react-router-dom";

import Navbar from "./components/navbar/Navbar";
import GuildSelectionScreen from "./screens/GuildSelectionScreen";
import LandingScreen from "./screens/LandingScreen";
import Footer from "./components/Footer";
import Callback from "./components/auth/Callback";
import {connect} from "react-redux";

const AuthenticatedRoute = ({component: Component, oauthCode, ...rest}) => (
    <Route
        {...rest}
        render={props =>
            oauthCode ?
                <Component {...rest} {...props} />
                :
                <Redirect to={{ pathname: "/login", state: { from: props.location }}} />

        }
    />
)


const App = ({oauthCode}) => {
    return (
        <div id="app" >
            <Navbar/>
            <Router>
                <Switch>
                    <Route path='/guilds'>
                        <AuthenticatedRoute oauthCode={oauthCode} path={'/guilds'} component={GuildSelectionScreen}/>
                    </Route>
                    <Route path='/auth/discord'>
                        <Callback path='/guilds'/>
                    </Route>
                    <Route path='/'>
                        <LandingScreen/>
                    </Route>
                </Switch>
            </Router>
            <Footer/>
        </div>

    );
};

const mapStateToProps = state => ({oauthCode: state.client.oauthCode})

export default connect(mapStateToProps) (App);
