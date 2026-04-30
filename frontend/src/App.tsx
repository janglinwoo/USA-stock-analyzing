import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Dashboard } from '@pages/Dashboard';
import './styles/index.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="bg-gray-900 text-white p-4 shadow-lg">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl">📈</span>
              <h1 className="text-xl font-bold">Stock Analyzer</h1>
            </div>
            <p className="text-sm text-gray-400">Real-time Prediction System</p>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>

        <footer className="bg-gray-900 text-gray-400 p-4 text-center text-sm">
          <p>
            USA Stock Analyzing System - Phases 1-5 Complete |{' '}
            <a href="https://github.com" className="text-blue-400 hover:text-blue-300">
              GitHub
            </a>
          </p>
        </footer>
      </div>
    </Router>
  );
}

export default App;
