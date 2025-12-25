import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Homepage from './Homepage';
import SymbolDetail from './SymbolDetail';
import List from './List';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/" element={<Homepage />} />
          <Route path="/symbol/:symbol" element={<SymbolDetail />} />
          <Route path="/list" element={<List />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
