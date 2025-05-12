import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StockPanel from './components/StockPanel'
import Home from './pages/Home';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/stocks/:symbol" element={<StockPanel />} />
      </Routes>
    </Router>
  );
}

export default App;

