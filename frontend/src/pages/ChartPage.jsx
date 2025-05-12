import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const symbols = ["AAPL", "TSLA", "BINANCE:BTCUSDT"];

  return (
    <div>
      <h1>주식 선택</h1>
      {symbols.map((sym) => (
        <button key={sym} onClick={() => navigate(`/chart/${encodeURIComponent(sym)}`)}>
          {sym}
        </button>
      ))}
    </div>
  );
}