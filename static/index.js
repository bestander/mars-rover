

function Video({ srcObject, ...props }) {
  const refVideo = React.useRef(null)

  React.useEffect(() => {
    if (!refVideo.current) return
    refVideo.current.srcObject = srcObject
  }, [srcObject])

  return <video ref={refVideo} {...props} />
}

const styles = {
  container: {
    height: "100%",
    width: "100%",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
  },
  turnButtonsContainer: {
    display: "flex",
    flexDirection: "row",
    height: "30%",
    width: "100%",
    justifyContent: "space-between",
  },
  verticalButton: {
    height: "30%",
    width: "30%",
  },
  horizontalButton: {
    width: "30%",
  },
};

class Controls extends React.Component {
  constructor(props) {
    super(props);
    this.state = { videoStream: null };
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
    return (
      <div style={styles.container}>
        <button
          style={styles.verticalButton}
          onClick={() =>
            this.connection.put_nowait(
              JSON.stringify({ action: "move", direction: "forward" })
            )
          }
        >
          Forward
        </button>
        <div style={styles.turnButtonsContainer}>
          <button
            style={styles.horizontalButton}
            onClick={() =>
              this.connection.put_nowait(
                JSON.stringify({ action: "move", direction: "left" })
              )
            }
          >
            Left
          </button>
          <Video autoplay playsinline controls srcObject = {this.state.videoStream}></Video> 
          <button
            style={styles.horizontalButton}
            onClick={() =>
              this.connection.put_nowait(
                JSON.stringify({ action: "move", direction: "right" })
              )
            }
          >
            Right
          </button>
        </div>
        <button
          style={styles.verticalButton}
          onClick={() =>
            this.connection.put_nowait(
              JSON.stringify({ action: "move", direction: "backward" })
            )
          }
        >
          Backward
        </button>
      </div>
    );
  }
}

ReactDOM.render(<Controls />, document.querySelector("#controls"));
