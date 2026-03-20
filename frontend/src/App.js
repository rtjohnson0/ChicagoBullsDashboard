// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const JSON_URL = 'https://raw.githubusercontent.com/rtjohnson0/ChicagoBullsDashboard/main/bulls_team_efficiency.json';

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(JSON_URL);
      setData(response.data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError('Failed to load data. Try refreshing.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch + auto-refresh every 60 seconds
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    fetchData();
  };

  if (loading && !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-black">
        <div className="text-3xl text-bullsRed animate-pulse">Loading Bulls Dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-black">
        <div className="text-xl text-red-400 bg-gray-900/70 p-8 rounded-2xl">{error}</div>
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
              Updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : data?.date || 'N/A'}
              <button onClick={handleRefresh} className="refresh-btn" aria-label="Refresh data">
                ↻ Refresh Now
              </button>
            </p>
          </div>
        </header>

        {/* Win Probability */}
        <section className="win-prob-section">
          <h2>Next Game Win Probability</h2>
          <div className="gauge-container">
            <CircularProgressbar
              value={50} // Replace with real calc later
              text={`${50}%`} // Placeholder — update with data
              styles={buildStyles({
                pathColor: '#CE1141',
                textColor: '#fff',
                trailColor: 'rgba(255,255,255,0.1)',
              })}
              aria-label="Estimated win probability for next game"
            />
          </div>
          <p className="next-game-info">
            vs {data?.next_game?.opponent || 'TBD'} ({data?.next_game?.is_home ? 'Home' : 'Away'})
          </p>
        </section>

        {/* Stats Grid */}
        <section className="stats-grid">
          <div className="stat-card glass-card">
            <h3>Offensive Rating</h3>
            <p className="stat-value">{data?.bulls_advanced?.off_rating?.toFixed(1) || 'N/A'}</p>
          </div>
          <div className="stat-card glass-card">
            <h3>Defensive Rating</h3>
            <p className="stat-value">{data?.bulls_advanced?.def_rating?.toFixed(1) || 'N/A'}</p>
          </div>
          <div className="stat-card glass-card">
            <h3>Net Rating</h3>
            <p className={`stat-value ${data?.bulls_advanced?.net_rating > 0 ? 'positive' : 'negative'}`}>
              {data?.bulls_advanced?.net_rating?.toFixed(1) || 'N/A'}
            </p>
          </div>
          <div className="stat-card glass-card">
            <h3>True Shooting %</h3>
            <p className="stat-value">{(data?.bulls_advanced?.ts_pct * 100)?.toFixed(1) || 'N/A'}%</p>
          </div>
          <div className="stat-card glass-card">
            <h3>Pace</h3>
            <p className="stat-value">{data?.bulls_advanced?.pace?.toFixed(1) || 'N/A'}</p>
          </div>
        </section>

        {/* Today's NBA Games (Live Ticker) */}
        {data?.all_games_today?.length > 0 && (
          <section className="games-ticker">
            <h2>Today's NBA Games</h2>
            <div className="games-grid">
              {data.all_games_today.map((game, i) => (
                <div 
                  key={i} 
                  className={`game-card glass-card ${game.is_live ? 'live-pulse' : ''}`}
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
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Injuries */}
        {data?.injuries?.length > 0 && (
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
                  {data.injuries.map((inj, i) => (
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