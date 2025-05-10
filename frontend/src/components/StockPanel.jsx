import { useEffect, useState } from "react";

export default function StockPanel() {
  const [price, setPrice] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => console.log("✅ WebSocket 연결 성공");
    ws.onerror = (e) => console.error("❌ WebSocket 에러", e);
    ws.onclose = () => console.warn("⚠️ WebSocket 연결 종료됨");
    ws.onmessage = (event) => {
      console.log("📩 수신된 메시지:", event.data);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        console.log("🧹 WebSocket 연결 종료 시도");
        ws.close();
      }
    };
  }, []);

  return (
    <div>
      <h2>AAPL 실시간 가격</h2>
      <p>{price ? `$${price}` : "⏳ 로딩 중..."}</p>
    </div>
  );
}
