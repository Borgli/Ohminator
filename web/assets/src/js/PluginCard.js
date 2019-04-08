import React from "react";


class PluginCard extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div>
                <div className="card">
                    <header className="card-header">
                        <p className="card-header-title">
                            Component
                        </p>
                        <a href="#" className="card-header-icon" aria-label="more options">
                      <span className="icon">
                        <i className="fas fa-angle-down" aria-hidden="true"></i>
                      </span>
                        </a>
                    </header>
                    <div className="card-content">
                        <div className="content">
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus nec iaculis mauris.
                            <a href="#">@bulmaio</a>. <a href="#">#css</a> <a href="#">#responsive</a>
                            <br/>
                                <time dateTime="2016-1-1">11:09 PM - 1 Jan 2016</time>
                        </div>
                    </div>
                    <footer className="card-footer">
                        <a href="#" className="card-footer-item">Save</a>
                        <a href="#" className="card-footer-item">Edit</a>
                        <a href="#" className="card-footer-item">Delete</a>
                    </footer>
                </div>
            </div>
        );
    }
}

export default PluginCard;