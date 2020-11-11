const domContainer = document.querySelector('#controls');
const e = React.createElement;

class Controls extends React.Component {
    constructor(props) {
        super(props);
        this.ws = new WebSocket("ws://127.0.0.1:8765/");
        this.ws.onmessage = function (event) {
            console.log("message", event);
        };
        this.state = { liked: false };
    }

    render() {
        return [
            e(
                'button',
                {
                    onClick: () => {
                        this.ws.send(JSON.stringify({ action: 'move', direction: "forward" }));
                    }
                },
                'Forward'
            ),
            e(
                'button',
                {
                    onClick: () => {
                        this.ws.send(JSON.stringify({ action: 'move', direction: "backward" }));
                    }
                },
                'Backward'
            )
        ];
    }
}

ReactDOM.render(e(Controls), domContainer);