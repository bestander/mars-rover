

const styles = {
  container: {
    height: "100%",
    width: "100%",
  },
  overlay: {
    position: "absolute",
    left: 0,
    right: 0,
    height: "10%",
    width: "100%",
    background: "green",
  },
  video: {
    position: "absolute",
    left: 0,
    right: 0,
    height: "100%",
    width: "100%",
  },
};

function Video({ srcObject, onStartPlayback, ...props }) {
  const refVideo = React.useRef(null)

  React.useEffect(() => {
    if (!refVideo.current) return
    refVideo.current.srcObject = srcObject;
  }, [srcObject])

  return <video ref={refVideo} {...props} />
}

class Controls extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      videoStream: null ,
  };

    const connection = new rtcbot.RTCConnection();
    this.connection = connection;
    connection.video.subscribe((stream) => {
      this.setState({ videoStream: stream });
    });
    connection.subscribe(m => console.log("Received from python:", m))

    async function connect() {
      let offer = await connection.getLocalDescription();
      let response = await fetch("/connect", {
        method: "POST",
        cache: "no-cache",
        body: JSON.stringify(offer)
      });

      await connection.setRemoteDescription(await response.json());
    }
    connect();
  }

  render() {
    return (<div style={styles.container}>
      <Video style={styles.video} playsinline autoplay controls srcObject={this.state.videoStream}></Video>
      <div style={styles.overlay}
        onMouseDown={(e) => {
          if (e.clientY < document.body.clientHeight / 3) {
            this.connection.put_nowait(
              JSON.stringify({ action: "move", direction: "forward" })
            )
          } else if (e.clientY > document.body.clientHeight * 2 / 3) {
            this.connection.put_nowait(
              JSON.stringify({ action: "move", direction: "backward" })
            )
          } else {
            if (e.clientX < document.body.clientWidth / 3) {
              this.connection.put_nowait(
                JSON.stringify({ action: "move", direction: "left" })
              )
            } else if (e.clientX > document.body.clientWidth * 2 / 3) {
              this.connection.put_nowait(
                JSON.stringify({ action: "move", direction: "right" })
              )
            }
          }
        }}
        onMouseUp={(e) => {
          this.connection.put_nowait(
            JSON.stringify({ action: "move", direction: "stop" })
          )
        }}
      >
      </div>
    </div>)
  }
}

ReactDOM.render(<Controls />, document.querySelector("#controls"));
