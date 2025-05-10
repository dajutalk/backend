import { useEffect, useState } from "react";

export default function StockPanel() {
  const [price, setPrice] = useState(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/stocks");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.data && data.data[0]) {
        setPrice(data.data[0].p);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div>
      <h2>AAPL 실시간 가격</h2>
      <p>{price ? `$${price}` : "Loading..."}</p>
    </div>
  );
}
