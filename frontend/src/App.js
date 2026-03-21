// frontend/src/App.jsx
import React from 'react';
import BullsStats from './components/BullsStats';
import NBAGamesTicker from './components/NBAGamesTicker';
import './App.css';

function App() {
  return (
    <div className="app-wrapper">
      <BullsStats />
      <NBAGamesTicker />
    </div>
  );
}

export default App;