// frontend/src/App.jsx
import React from 'react';
import BullsStats from './components/BullsStats';
import NBAGamesTicker from './components/NBAGamesTicker';
import WinProbability from './components/WinProbability';
import './App.css';
import BullsTrends from './components/BullsTrend';

function App() {
  return (
    <div className="app-wrapper">
      <BullsStats />
      <BullsTrends />
      <NBAGamesTicker />
     <WinProbability />
    </div>
  );
}

export default App;