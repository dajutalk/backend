import { useParams} from "react-router-dom"
import StockPanel from "../components/StockPanel";
import ChatPanel from "../components/ChatPanel";

export default function StockPage() {
  const { symbol } = useParams();
  return (
    <div style={{ display: "flex", gap: "2rem" }}>
      <StockPanel symbol={symbol} />
      <ChatPanel symbol={symbol} />
    </div>
  );
}
