// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import './App.css';

function App() {
  const BULLS_URL = 'https://raw.githubusercontent.com/rtjohnson0/ChicagoBullsDashboard/main/bulls_daily.json';
  const SCOREBOARD_URL = 'https://raw.githubusercontent.com/rtjohnson0/ChicagoBullsDashboard/main/nba_today_games.json';

  const [bullsData, setBullsData] = useState(null);
  const [scoreboardData, setScoreboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [bullsRes, scoreboardRes] = await Promise.all([
        axios.get(BULLS_URL),
        axios.get(SCOREBOARD_URL)
      ]);
      setBullsData(bullsRes.data);
      setScoreboardData(scoreboardRes.data);
      setLastUpdated(new Date());
      console.log('Data refreshed successfully');
    } catch (err) {
      setError('Failed to load data. Check console or try again.');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Initial load + auto-refresh every 60 seconds
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    fetchAll();
  };

  if (loading && !bullsData && !scoreboardData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-black">
        <div className="text-3xl text-bullsRed animate-pulse">Loading Bulls Dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-black">
        <div className="text-xl text-red-400 bg-gray-900/80 p-8 rounded-2xl text-center max-w-md">
          {error}
          <button 
            onClick={handleRefresh}
            className="mt-6 px-6 py-3 bg-bullsRed text-white rounded-lg hover:bg-red-600 transition"
          >
            Try Refreshing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-black to-gray-900 text-white">
      <div className="app-container">
        {/* Header */}
        <header className="header">
          <h1>Chicago Bulls Daily Efficiency Dashboard</h1>
          <div className="update-info">
            <p>
              Updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : bullsData?.date || 'N/A'}
              <button onClick={handleRefresh} className="refresh-btn" aria-label="Refresh data">
                ↻ Refresh Now
              </button>
            </p>
          </div>
        </header>

        {/* Win Probability (placeholder calc - update with real logic later) */}
        <section className="win-prob-section">
          <h2>Next Game Win Probability</h2>
          <div className="gauge-container">
            <CircularProgressbar
              value={bullsData?.calculated?.expected_win_pct || 50}
              text={`${bullsData?.calculated?.expected_win_pct || 'N/A'}%`}
              styles={buildStyles({
                pathColor: (bullsData?.calculated?.expected_win_pct || 50) > 50 ? '#CE1141' : '#ef4444',
                textColor: '#fff',
                trailColor: 'rgba(255,255,255,0.1)',
              })}
              aria-label="Estimated win probability for next game"
            />
          </div>
          <p className="next-game-info">
            vs {bullsData?.next_game?.opponent || 'TBD'} ({bullsData?.next_game?.is_home ? 'Home' : 'Away'})
          </p>
        </section>

        {/* Stats Grid */}
        <section className="stats-grid">
          <div className="stat-card glass-card">
            <h3>Offensive Rating</h3>
            <p className="stat-value">{bullsData?.bulls_advanced?.off_rating?.toFixed(1) || 'N/A'}</p>
          </div>
          <div className="stat-card glass-card">
            <h3>Defensive Rating</h3>
            <p className="stat-value">{bullsData?.bulls_advanced?.def_rating?.toFixed(1) || 'N/A'}</p>
          </div>
          <div className="stat-card glass-card">
            <h3>Net Rating</h3>
            <p className={`stat-value ${bullsData?.bulls_advanced?.net_rating > 0 ? 'positive' : 'negative'}`}>
              {bullsData?.bulls_advanced?.net_rating?.toFixed(1) || 'N/A'}
            </p>
          </div>
          <div className="stat-card glass-card">
            <h3>True Shooting %</h3>
            <p className="stat-value">{(bullsData?.bulls_advanced?.ts_pct * 100)?.toFixed(1) || 'N/A'}%</p>
          </div>
          <div className="stat-card glass-card">
            <h3>Pace</h3>
            <p className="stat-value">{bullsData?.bulls_advanced?.pace?.toFixed(1) || 'N/A'}</p>
          </div>
        </section>

        {/* Today's NBA Games Ticker */}
        {scoreboardData?.all_games_today?.length > 0 && (
          <section className="games-ticker">
            <h2>Today's NBA Games</h2>
            <div className="games-grid">
              {scoreboardData.all_games_today.map((game, i) => (
                <div 
                  key={i} 
                  className={`game-card glass-card ${game.is_live ? 'live-pulse' : game.is_completed ? 'completed' : ''}`}
                >
                  <p className="matchup">
                    {game.away_team} @ {game.home_team}
                  </p>
                  <p className="score">
                    {game.score !== 'N/A' ? game.score : game.status}
                  </p>
                  {game.is_live && (
                    <p className="live-info">
                      Q{game.quarter} • {game.time_remaining}
                    </p>
                  )}
                  {game.is_completed && (
                    <p className="completed-info">Final</p>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Injuries */}
        {bullsData?.injuries?.length > 0 && (
          <section className="injuries-section">
            <h2>Current Injuries</h2>
            <div className="table-container">
              <table className="injuries-table">
                <thead>
                  <tr>
                    <th>Player</th>
                    <th>Position</th>
                    <th>Injury</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {bullsData.injuries.map((inj, i) => (
                    <tr key={i}>
                      <td>{inj.player}</td>
                      <td>{inj.position}</td>
                      <td>{inj.injury}</td>
                      <td className={
                        inj.status.toLowerCase().includes('out') ? 'status-out' :
                        inj.status.toLowerCase().includes('questionable') ? 'status-questionable' :
                        'status-probable'
                      }>
                        {inj.status}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <footer className="footer">
          <p>Data from NBA API • Auto-refreshes every 60s • Powered by GitHub Actions</p>
        </footer>
      </div>
    </div>
  );
}

export default App;