const styles = {
  container: {
    height: "100%",
    width: "100%",
  },
  overlay: {
    position: "absolute",
    left: 0,
    right: 0,
    height: "100%",
    width: "100%",
    background: "transparent",
  },
  video: {
    position: "absolute",
    left: 0,
    right: 0,
    height: "100%",
    width: "100%",
  },
};

function Controls() {
  const [connection, setConnection] = React.useState(null);
  const [isVideoStarted, setVideoStarted] = React.useState(false);
  const refVideo = React.useRef(null);

  const playVideo = () => {
    if (refVideo.current && refVideo.current.srcObject && !isVideoStarted) {
      setVideoStarted(true);
      refVideo.current.play();
    }
  };

  React.useEffect(async () => {
    const newConnection = new rtcbot.RTCConnection();
    newConnection.video.subscribe((stream) => {
      refVideo.current.srcObject = stream;
    });
    newConnection.subscribe(m => console.log("Received from python:", m))
    const offer = await newConnection.getLocalDescription();
    const response = await fetch("/connect", {
      method: "POST",
      cache: "no-cache",
      body: JSON.stringify(offer)
    });
    await newConnection.setRemoteDescription(await response.json());
    setConnection(newConnection);
  }, [])

  return (<div style={styles.container}>
    <video ref={refVideo} style={styles.video} playsinline autoplay controls />
    <div style={styles.overlay}
      onMouseDown={(e) => {
        playVideo();
        if (e.clientY < document.body.clientHeight / 3) {
          connection.put_nowait(
            JSON.stringify({ action: "move", direction: "forward" })
          )
        } else if (e.clientY > document.body.clientHeight * 2 / 3) {
          connection.put_nowait(
            JSON.stringify({ action: "move", direction: "backward" })
          )
        } else {
          if (e.clientX < document.body.clientWidth / 3) {
            connection.put_nowait(
              JSON.stringify({ action: "move", direction: "left" })
            )
          } else if (e.clientX > document.body.clientWidth * 2 / 3) {
            connection.put_nowait(
              JSON.stringify({ action: "move", direction: "right" })
            )
          }
        }
      }}
      onMouseUp={(e) => {
        connection.put_nowait(
          JSON.stringify({ action: "move", direction: "stop" })
        )
      }}
    >
    </div>
  </div>)
}

ReactDOM.render(<Controls />, document.querySelector("#controls"));
