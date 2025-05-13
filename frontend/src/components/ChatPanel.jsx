import { useEffect, useState } from "react";

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/chat");

    ws.onmessage = (event) => {
      setMessages((prev) => [...prev, event.data]);
    };

    return () => ws.close();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const ws = new WebSocket("ws://localhost:8000/ws/chat");
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
