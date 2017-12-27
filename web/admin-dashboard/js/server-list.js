const e = React.createElement;
let container;

function websocket() {
  var ws = new WebSocket("ws://127.0.0.1:5678/");
  ws.onopen = function (ev) {
    console.log('open');
    ws.send('get_servers');
    console.log('sent')
  };

  ws.onmessage = function (ev) {
    console.log(ev.data);
    let servers = JSON.parse(ev.data);
    let tableRows = [];
    for (let server of servers) {
      tableRows.push(<TableRow items={server}/>);
    }
    let components = [<Table itemNames={["Name", "ID", "Population"]}>{tableRows}</Table>, <div id={"chart"}/>];
    container.setState({overlay: false, content: components});
    let columns = [];
    for (let server of servers) {
      columns.push([server['name'], server['population']])
    }
    let chart = bb.generate({
      bindto: "#chart",
      data: {
          type: "donut",
          columns: columns
      },
      donut: {
        title: "Server Populations"
      }
    });
  };
  ws.onerror = function (ev) {
    console.log(ev);
  };

  ws.onclose = function (ev) {
    console.log("Connection Closed!");
  };
}

class ServerListCard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {rows: null, overlay: true};
    this.ws = new WebSocket("ws://127.0.0.1:5678/");
    this.ws.onopen = (ev) => {
      console.log('open');
      this.ws.send('get_servers');
      console.log('sent')
    };
    this.ws.onmessage = (ev) => {
      console.log(ev.data);
      let servers = JSON.parse(ev.data);
      this.setState({overlay: false, rows: servers.map((server) => <TableRow key={server.id} items={server}/>)});
      let columns = [];
      for (let server of servers) {
        columns.push([server['name'], server['population']])
      }
      let chart = bb.generate({
        bindto: "#chart",
        data: {
            type: "donut",
            columns: columns
        },
        donut: {
          title: "Server Populations"
        }
      });
    };
  }

  render() {
    return (
      <Card width={"12"} title={"Server List"} overlay={this.state.overlay}>
        <Table itemNames={["Name", "ID", "Population"]}>
          {this.state.rows}
        </Table>
        <div id={"chart"} />
      </Card>
    );
  }
}

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

function renderReact() {
  container = ReactDOM.render(
    <Row>
      <ServerListCard width={"12"} title={"Server List"}/>
    </Row>,
    document.getElementById('container')
  );
}

function init() {
  renderReact();
}

document.addEventListener('DOMContentLoaded', init, false);
