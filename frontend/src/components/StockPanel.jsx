import { useEffect, useState } from "react";
import {  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid } from "recharts";

export default function StockPanel() {

  const [symbol, setSymbol] = useState(null);
  const [volume, setVolume] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
 
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/stocks");

    ws.onopen = () => console.log("WebSocket 연결 성공");

    ws.onmessage = (event) => {
      console.log(" 수신된 메시지:", event.data);
      try {
        const data = JSON.parse(event.data);
        if (data.data && data.data[0]) {
          const btc = data.data.find(t => t.s === "BINANCE:BTCUSDT");
          if (btc){
            setSymbol(btc.s);
            
            setVolume(btc.v);
            setPriceHistory((prev) => [...prev, {time: new Date, price: btc.p}]);
            
          }
        }
      } catch (e) {
        //  만약 그냥 문자열이면 여기에 예외처리됨
        if (event.data === "ping") {
          console.log("ping 수신됨");
        }
      }
    };

    ws.onerror = (e) => console.error(" WebSocket 에러", e);
    ws.onclose = () => console.warn(" WebSocket 연결 종료됨");

    return () => {
      console.log(" WebSocket 연결 종료 시도");
      ws.close();
    };
  }, [])

  return (
    <div>
      <h2>{symbol ? `${symbol}`: "로딩 중"}</h2>
      <LineChart width={600} height={300} data={priceHistory}>
        <XAxis dataKey="time" />
        <YAxis domain={['auto', 'auto']} />
        <CartesianGrid stroke="#ccc" />
        <Tooltip />
        <Line type="monotone" dataKey="price" stroke="#8884d8" />
      </LineChart>
      <p>{volume ? `거래량: ${volume}` : "로딩 중"}</p>
    </div>
  );
}
