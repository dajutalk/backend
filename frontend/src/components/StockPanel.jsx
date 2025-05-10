import { useEffect, useState } from "react";

export default function StockPanel() {
  const [price, setPrice] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/stocks");

    ws.onopen = () => console.log("✅ WebSocket 연결 성공");

    ws.onmessage = (event) => {
      console.log("📩 수신된 메시지:", event.data);
      try {
        const data = JSON.parse(event.data);
        if (data.data && data.data[0]) {
          const btc = data.data.find(t => t.s === "BINANCE:BTCUSDT");
          if (btc) setPrice(btc.p);
        }
      } catch (e) {
        // 👉 만약 그냥 문자열이면 여기에 예외처리됨
        if (event.data === "pong") {
          setPrice("💡 pong 수신됨");
        }
      }
    };

    ws.onerror = (e) => console.error("❌ WebSocket 에러", e);
    ws.onclose = () => console.warn("⚠️ WebSocket 연결 종료됨");

    return () => {
      console.log("🧹 WebSocket 연결 종료 시도");
      ws.close();
    };
  }, [])

  return (
    <div>
      <h2>실시간 가격</h2>
      <p>{price ? `$${price}` : "⏳ 로딩 중..."}</p>
    </div>
  );
}
