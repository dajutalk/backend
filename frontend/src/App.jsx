import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import StockPage from './pages/StockPage'
import Home from './pages/Home';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/stocks/:symbol" element={<StockPage />} />
      </Routes>
    </Router>
  );
}

export default App;

