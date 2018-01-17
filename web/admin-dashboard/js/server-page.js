class ServerInfoCard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {rows: null, overlay: true};
    this.ws = new WebSocket("ws://127.0.0.1:5678/");
    this.ws.onopen = (ev) => {
      this.ws.send('get_server_info');
      this.ws.send(new URL(window.location.href).searchParams.get("server_id"));
    };
    this.ws.onmessage = (ev) => {
      console.log(JSON.parse(ev.data));
      let server = JSON.parse(ev.data);
      let display_members = server.members.map((member) => [member.name, member.id, member.bot ? "true": "false",
        member.top_role.name, member.created_at, member.joined_at]);
      this.setState({overlay: false, rows: display_members.map((member, index) =>
          <TableRow key={index} items={member} />)});
      ReactDOM.render(
        <ServerPageTitle title={"Server Page"} subtitle={"Overview over the server " + server.name}/>,
        document.getElementById('title')
      );
    };
  }

  render() {
    return (
      <Card width={"12"} title={"Member List"} overlay={this.state.overlay}>
        <Table itemNames={["Name", "ID", "Bot", "Top Role", "Created at", "Joined at"]} hoverable={true}>
          {this.state.rows}
        </Table>
        <div id={"chart"} />
      </Card>
    );
  }
}

class ServerPageTitle extends React.Component {
  render() {
    return (
      <PageTitle title={this.props.title} subtitle={this.props.subtitle}>
        <Breadcrumb>
          <BreadcrumbEntry link={"server-list.html"}>Server List</BreadcrumbEntry>
          <BreadcrumbEntry link={"#"}>Server Page</BreadcrumbEntry>
        </Breadcrumb>
      </PageTitle>
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

  ReactDOM.render(
    <ServerPageTitle title={"Loading"} subtitle={""}/>,
    document.getElementById('title')
  );
}

function init() {
  renderReact();
}

document.addEventListener('DOMContentLoaded', init, false);
