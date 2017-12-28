
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
      <table className={"table"}>
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
    return <tr>{rows}</tr>;
  }
}