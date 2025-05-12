import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const symbols = ["AAPL", "TSLA", "BINANCE:BTCUSDT"];

return (
    <div>
      <h1>종목 선택</h1>
      <button onClick={() => navigate('/stock/AAPL')}>AAPL</button>
      <button onClick={() => navigate('/stock/TSLA')}>TSLA</button>
      <button onClick={() => navigate('/stock/BINANCE:BTCUSDT')}>BTCUSDT</button>
    </div>
  );
}