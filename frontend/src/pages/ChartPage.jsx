import { useParams } from "react-router-dom";
import StockChart from "../components/StockChart";

export default function ChartPage() {
  const { symbol } = useParams();  // AAPL, TSLA, etc
  return (
    <div>
      <h2>{symbol} 실시간 차트</h2>
      <StockChart symbol={symbol} />
    </div>
  );
}