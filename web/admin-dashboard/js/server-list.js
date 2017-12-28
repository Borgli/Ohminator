class ServerListCard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {rows: null, overlay: true};
    this.ws = new WebSocket("ws://127.0.0.1:5678/");
    this.ws.onopen = (ev) => {
      this.ws.send('get_servers');
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

function renderReact() {
  ReactDOM.render(
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
