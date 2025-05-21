import { useNavigate } from "react-router-dom";

export default function Home() {
  const navigate = useNavigate();


return (
    <div>
      <h1>종목 선택</h1>
      <button onClick={() => navigate('/stocks/BINANCE:ETHUSDT')}>이더리움</button>
      <button onClick={() => navigate('/stocks/BINANCE:BNBUSDT')}>바이낸스</button>
      <button onClick={() => navigate('/stocks/BINANCE:BTCUSDT')}>비트코인</button>
      <button onClick={() => navigate('/stocks/BINANCE:SOLUSDT')}>솔라나</button>


    </div>
  );
}