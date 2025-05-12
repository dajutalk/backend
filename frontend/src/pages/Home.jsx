import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();
  const symbols = ["AAPL", "TSLA", "BINANCE:BTCUSDT"];

return (
    <div>
      <h1>종목 선택</h1>
      <button onClick={() => navigate('/stocks/AAPL')}>AAPL</button>
      <button onClick={() => navigate('/stocks/TSLA')}>TSLA</button>
      <button onClick={() => navigate('/stocks/BINANCE:BTCUSDT')}>BTCUSDT</button>
    </div>
  );
}