
class Overlay extends React.Component {
  render() {
    return (
      <div className={"overlay"}>
        <div className={"m-loader mr-20"}>
          <svg className={"m-circular"} viewBox={"25 25 50 50"}>
            <circle className={"path"} cx="50" cy="50" r="20" fill="none" strokeWidth="4" strokeMiterlimit="10"/>
          </svg>
        </div>
        <h3 className={"l-text"}>Loading</h3>
      </div>);
  }
}

class Row extends React.Component {
  render() {
    return <div className={"row"}>{this.props.children}</div>;
  }
}

class Card extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className={"col-md-" + this.props.width}>
        <div className={"card"}>
          <div className={"card-body"}>
            {this.props.overlay ? <Overlay /> : null}
            <h3 className={"card-title"}>{this.props.title}</h3>
            {this.props.children}
          </div>
        </div>
      </div>
    );
  }
}

class Table extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    let rows = this.props.itemNames;
    rows = rows.map((item, index) => <th key={index}>{item}</th>);
    return (
      <table className={"table" + (this.props.hoverable ? " table-hover" : "")}>
        <thead>
          <tr>
            {rows}
          </tr>
        </thead>
        <tbody>
          {this.props.children}
        </tbody>
      </table>
    );
  }
}

class TableRow extends React.Component {
  render() {
    let items = this.props.items;
    let rows = Object.values(items).map((item, index) => <td key={index}>{item}</td>);
    return <tr onClick={this.props.onClickHandler ? this.props.onClickHandler : null}>{rows}</tr>;
  }
}

class PageTitle extends React.Component {
  render() {
    return (
      <div className={"page-title"}>
        <div>
          <h1><i className={"fa fa-dashboard"}/> {this.props.title}</h1>
          <p>{this.props.subtitle}</p>
        </div>
        {this.props.children}
      </div>
    );
  }
}

class Breadcrumb extends React.Component {
  render() {
    return (
      <div>
        <ul className="breadcrumb">
          <li><i className="fa fa-home fa-lg"/></li>
          {this.props.children}
        </ul>
      </div>
    );
  }
}

class BreadcrumbEntry extends React.Component {
  render() {
    if (this.props.link) {
      return(<li className={"breadcrumb-item active"}>this.props.children</li>);
    } else {
      return(<li className={"breadcrumb-item"}><a href={this.props.link}>{this.props.children}</a>);
    }
  }
}
