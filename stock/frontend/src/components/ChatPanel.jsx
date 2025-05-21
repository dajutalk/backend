import { useEffect, useState } from "react";
import {useParams} from "react-router-dom"

export default function ChatPanel() {
  const {symbol } = useParams();
  const [input, setInput] = useState("");


  const handleSubmit = (e) => {
    e.preventDefault();
    const ws = new WebSocket(`ws://localhost:8000/ws/chat?symbol=${symbol}`);
    ws.onopen = () => {
      ws.send(input);
      ws.close();
    };
    setInput("");
  };

  return (
    <div>
      <h2>실시간 채팅</h2>
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={(e) => setInput(e.target.value)} />
        <button type="submit">보내기</button>
      </form>
      <ul>
        {messages.map((msg, idx) => <li key={idx}>{msg}</li>)}
      </ul>
    </div>
  );
}
