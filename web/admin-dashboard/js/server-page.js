class ServerInfoCard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {rows: null, overlay: true};
    this.ws = new WebSocket("ws://127.0.0.1:5678/");
    this.ws.onopen = (ev) => {
      this.ws.send('get_server_info');
      this.ws.send('375059981663338496');
    };
    this.ws.onmessage = (ev) => {
      console.log(JSON.parse(ev.data));
      let server = JSON.parse(ev.data);
      let display_members = server.members.map((member) => [member.name, member.id, member.bot ? "true": "false",
        member.top_role.name, member.created_at, member.joined_at]);
      this.setState({overlay: false, rows: display_members.map((member, index) =>
          <TableRow key={index} items={member} />)});
    };
  }

  render() {
    return (
      <Card width={"12"} title={"Member List"} overlay={this.state.overlay}>
        <Table itemNames={["Name", "ID", "Bot", "Top Role", "Created at", "Joined at"]}>
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
      <ServerInfoCard width={"12"} title={"Server List"}/>
    </Row>,
    document.getElementById('container')
  );
}

function init() {
  renderReact();
}

document.addEventListener('DOMContentLoaded', init, false);