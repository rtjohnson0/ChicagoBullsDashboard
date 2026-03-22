// frontend/src/App.jsx
import React from 'react';
import BullsStats from './components/BullsStats';
import NBAGamesTicker from './components/NBAGamesTicker';
import WinProbability from './components/WinProbability';
import './App.css';

function App() {
  return (
    <div className="app-wrapper">
      <BullsStats />
      <NBAGamesTicker />
     <WinProbability />
    </div>
  );
}

export default App;