import StockPanel from "../components/StockPanel";
import ChatPanel from "../components/ChatPanel";

export default function StockPage() {
  return (
    <div style={{ display: "flex", gap: "2rem" }}>
      <StockPanel />
      <ChatPanel />
    </div>
  );
}
