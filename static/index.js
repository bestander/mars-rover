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

  const pointerDown = (e) => {
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
    </div>
  </div>)
}

ReactDOM.render(<Controls />, document.querySelector("#controls"));
