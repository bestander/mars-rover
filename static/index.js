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
  const [message, setMessage] = React.useState('Rober not connected');
  const [isVideoStarted, setVideoStarted] = React.useState(false);
  const refVideo = React.useRef(null);

  const playVideo = () => {
    if (connection && refVideo.current && refVideo.current.srcObject && !isVideoStarted) {
      setMessage(null);
      setVideoStarted(true);
      refVideo.current.play();
    }
  };

  const pointerDown = (e) => {
    if (!connection) {
      return;
    }
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
  }

  const pointerUp = () => {
    if (!connection) {
      return;
    }
    connection.put_nowait(
      JSON.stringify({ action: "move", direction: "stop" })
    )
  }

  React.useEffect(async () => {
    const newConnection = new rtcbot.RTCConnection();
    newConnection.video.subscribe((stream) => {
      refVideo.current.srcObject = stream;
    });
    newConnection.subscribe(m => console.log("Received from python:", m))
    const offer = await newConnection.getLocalDescription();
    const response = await fetch("/negotiateRtcConnectionWithRobot", {
      method: "POST",
      cache: "no-cache",
      body: JSON.stringify(offer)
    });
    await newConnection.setRemoteDescription(await response.json());
    setMessage('Robot found: click to start driving');
    setConnection(newConnection);
  }, [])

  return (<div style={styles.container}>
    <video ref={refVideo} style={styles.video} webkit-playsinline="true" playsinline="true" />
    <div style={styles.overlay}
      onContextMenu={(e) => {
          e.preventDefault();
      }}
      onClick={() => {
        playVideo();
      }}
      onMouseDown={(e) => {
        pointerDown(e)
      }}
      onPointerDown={(e) => {
        pointerDown(e)
      }}
      onMouseUp={() => {
        pointerUp()
      }}
      onPointerUp={() => {
        pointerUp()
      }}
    >
      {message}
    </div>
  </div>)
}

ReactDOM.render(<Controls />, document.querySelector("#controls"));
