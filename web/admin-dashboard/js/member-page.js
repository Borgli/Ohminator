class MemberInfoCard extends React.Component {
  constructor(props) {
    super(props);
    this.state = {overlay: true, memberName: "Loading"};
    this.ws = new WebSocket("ws://127.0.0.1:5678/");
    this.ws.onopen = (ev) => {
      this.ws.send('get_member_info');
      this.ws.send(new URL(window.location.href).searchParams.get("server_id"));
      this.ws.send('get_yt_list');
    };
    this.ws.onmessage = (ev) => {
      console.log(JSON.parse(ev.data));
      let server = JSON.parse(ev.data);
      this.member = server.members.find((member) => member.id === new URL(window.location.href).searchParams.get("member_id"));
      if (!this.member) {
        console.log("No member with that id!");
      }
      this.setState({overlay: false, memberName: this.member.name});
      ReactDOM.render(
        <MemberPageTitle title={"Member Page"} subtitle={"Overview over user " + this.member.name}/>,
        document.getElementById('title')
      );
    };
  }

  render() {
    return (
      <Card width={"12"} title={this.state.memberName} overlay={this.state.overlay}>
        {this.member && <img src={this.member.avatar_url === "" ?
          this.member.default_avatar_url : this.member.avatar_url} className={"img-circle"}
          width={"96px"} height={"96px"}/>}
      </Card>
    );
  }
}

class MemberPageTitle extends React.Component {
  render() {
    return (
      <PageTitle title={this.props.title} subtitle={this.props.subtitle}>
        <Breadcrumb>
          <BreadcrumbEntry link={"server-list.html"}>Server List</BreadcrumbEntry>
          <BreadcrumbEntry link={"server-page.html?server_id=" +
          new URL(window.location.href).searchParams.get("server_id")}>Server Page</BreadcrumbEntry>
          <BreadcrumbEntry>Member Page</BreadcrumbEntry>
        </Breadcrumb>
      </PageTitle>
    );
  }
}

function renderReact() {
  ReactDOM.render(
    <Row>
      <MemberInfoCard width={"12"} title={"Member List"}/>
    </Row>,
    document.getElementById('container')
  );

  ReactDOM.render(
    <MemberPageTitle title={"Loading"} subtitle={""}/>,
    document.getElementById('title')
  );
}

function init() {
  renderReact();
}

document.addEventListener('DOMContentLoaded', init, false);
