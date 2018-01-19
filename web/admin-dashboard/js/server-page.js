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
      let response = JSON.parse(ev.data);
      if (response["response"] === "server") {
        let server = response["data"];
        let display_members = server.members.map((member) => [member.name, member.id, member.bot ? "true" : "false",
          member.top_role.name, member.created_at, member.joined_at]);
        this.setState({
          overlay: false, rows: display_members.map((member, index) =>
            <TableRow onClickHandler={() => {
              window.location.href = "member-page.html?server_id=" + server.id
                + "&member_id=" + member[1]
            }} key={index} items={member}/>)
        });
        ReactDOM.render(
          <ServerPageTitle title={"Server Page"} subtitle={"Overview over the server " + server.name}/>,
          document.getElementById('title')
        );
      }
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

class YoutubePlaylist extends React.Component {
  constructor(props) {
    super(props);
    this.state = {overlay: true, rows: null, currently_playing: "Nothing is currently playing"};
    this.ws = new WebSocket("ws://127.0.0.1:5678/");
    this.ws.onopen = (ev) => {
      this.ws.send('get_yt_list');
      this.ws.send(new URL(window.location.href).searchParams.get("server_id"));
    };
    this.ws.onmessage = (ev) => {
      console.log(JSON.parse(ev.data));
      let response = JSON.parse(ev.data);
      if (response["response"] === "yt_playlist") {
        this.yt_playlist = response["data"];
        let display_list = this.yt_playlist["queue"].map((entry) => [
            <div>
              <a href={"https://www.youtube.com/watch?v=" + entry.webpage_url}/>
              < img src={"https://i.ytimg.com/vi/" + entry.thumbnail + "/mqdefault.jpg"} className={"img-responsive"}/>
            </div>,
            entry.title
          ]);
        this.setState({overlay: false,
          rows: display_list.map((entry, index) =>
          <TableRow key={index} items={entry}/>),
          currently_playing: this.yt_playlist["currently_playing"].title});
      }
    };
  }

  render() {
    return (
      <Card width={"6"} title={"Youtube Playlist"} overlay={this.state.overlay}>
        <CurrentlyPlaying songName={this.state.currently_playing}/>
        <Table itemNames={["Thumbnail", "Song Name"]} hoverable={true}>
          {this.state.rows}
        </Table>
      </Card>
    );
  }
}

class CurrentlyPlaying extends React.Component {
  render() {
    return (
      <div>
        <h4>{this.props.songName}</h4>
        <div id={"currently_playing_bar"} />
      </div>
    );
  }
}

class ServerPageTitle extends React.Component {
  render() {
    return (
      <PageTitle title={this.props.title} subtitle={this.props.subtitle}>
        <Breadcrumb>
          <BreadcrumbEntry link={"server-list.html"}>Server List</BreadcrumbEntry>
          <BreadcrumbEntry>Server Page</BreadcrumbEntry>
        </Breadcrumb>
      </PageTitle>
    );
  }
}

function renderReact() {
  ReactDOM.render(
    <Row>
      <ServerInfoCard width={"12"} title={"Server List"}/>
      <YoutubePlaylist/>
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
