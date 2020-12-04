const styles = {
  container: {
    height: "100%",
    width: "100%",
    display: "flex",
    flexDirection: "column"
  },
  videoContainer: {
    position: "relative",
    height: "90%",
    width: "100%",
  },
  overlay: {
    position: "absolute",
    left: 0,
    right: 0,
    height: "100%",
    width: "100%",
    background: "transparent",
    "textAlign": "center",
    "lineHeight": 10,
    "fontFamily": "sans-serif",
    "fontSize": "x-large",
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
  const [message, setMessage] = React.useState('Rover not connected');
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
    try {
      const response = await fetch("/negotiateRtcConnectionWithRobot", {
        method: "POST",
        cache: "no-cache",
        body: JSON.stringify(offer)
      });
      await newConnection.setRemoteDescription(await response.json());
    } catch (e) {
      console.log(e);
      return;
    }
    setMessage('Rover connected: click to start driving');
    setConnection(newConnection);
  }, [])

  return (
    <div style={styles.container}>
      <div style={styles.videoContainer}>
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
      </div>
      <HSLControl connection={connection}></HSLControl>
    </div>
  )
}

const hslStyles = {
  container: {
    display: "flex",
    flexDirection: "column"
  },
  row: {
  },
}

function HSLControl(props) {
  const [hsv, setHSV] = React.useState({
    hueMin: 0,
    hueMax: 255,
    satMin: 0,
    satMax: 180,
    valMin: 0,
    valMax: 255,
  });

  React.useEffect(() => {
    if (props.connection) {
      props.connection.put_nowait(
        JSON.stringify({ action: "hsv", hsv })
      )
    }
  }, [hsv])

  return (<div style={hslStyles.container}>
    <div style={hslStyles.row}>
      Hue
    <input type="range"
        min={0}
        max={hsv.hueMax}
        step={1}
        defaultValue={hsv.hueMin}
        onMouseUp={(e) => {
          setHSV({ ...hsv, hueMin: +e.target.value });
        }}
      ></input><span>{hsv.hueMin}</span>
      <input type="range"
        min={hsv.hueMin}
        max={255}
        step={1}
        defaultValue={hsv.hueMax}
        onMouseUp={(e) => {
          setHSV({ ...hsv, hueMax: +e.target.value });
        }}
      ></input><span>{hsv.hueMax}</span>
    </div>
    <div style={hslStyles.row}>
      Saturation
    <input type="range"
        min={0}
        max={hsv.satMax}
        step={1}
        defaultValue={hsv.satMin}
        onMouseUp={(e) => {
          setHSV({ ...hsv, satMin: +e.target.value });
        }}
      ></input><span>{hsv.satMin}</span>
      <input type="range"
        min={hsv.satMin}
        max={180}
        step={1}
        defaultValue={hsv.satMax}
        onMouseUp={(e) => {
          setHSV({ ...hsv, satMax: +e.target.value });
        }}
      ></input><span>{hsv.satMax}</span>
    </div>
    <div style={hslStyles.row}>
      Value
    <input type="range"
        min={0}
        max={hsv.valMax}
        step={1}
        defaultValue={hsv.valMin}
        onMouseUp={(e) => {
          setHSV({ ...hsv, valMin: +e.target.value });
        }}
      ></input><span>{hsv.valMin}</span>
      <input type="range"
        min={hsv.valMin}
        max={180}
        step={1}
        defaultValue={hsv.valMax}
        onMouseUp={(e) => {
          setHSV({ ...hsv, valMax: +e.target.value });
        }}
      ></input><span>{hsv.valMax}</span>
    </div>
  </div>)
}

ReactDOM.render(<Controls />, document.querySelector("#controls"));
