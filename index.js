const domContainer = document.querySelector("#controls");

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
    this.ws = new WebSocket(`ws://${window.location.hostname}:8765/`);
    this.ws.onmessage = function (event) {
      console.log("message", event);
    };
    this.state = { liked: false };
  }

  render() {
    return (
      <div style={styles.container}>
        <button
          style={styles.verticalButton}
          onClick={() =>
            this.ws.send(
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
              this.ws.send(
                JSON.stringify({ action: "move", direction: "left" })
              )
            }
          >
            Left
          </button>
          <button
            style={styles.horizontalButton}
            onClick={() =>
              this.ws.send(
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
            this.ws.send(
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

ReactDOM.render(<Controls />, domContainer);
