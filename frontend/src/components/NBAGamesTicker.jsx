// src/components/NBAGamesTicker.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './NBAGamesTicker.css';

const SCOREBOARD_URL = 'https://raw.githubusercontent.com/rtjohnson0/ChicagoBullsDashboard/main/nba_today_games.json';

function NBAGamesTicker() {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchGames = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(SCOREBOARD_URL);
      setGames(res.data.all_games_today || []);
      setLastUpdated(new Date());
      console.log('Live games loaded:', res.data.all_games_today);
    } catch (err) {
      setError('Failed to load today\'s NBA games.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGames();
    const interval = setInterval(fetchGames, 30000); // 30 seconds for live updates
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => fetchGames();

  if (loading && games.length === 0) {
    return <div className="loading">Loading today's NBA games...</div>;
  }

  if (error) {
    return (
      <div className="error-message">
        {error}
        <button onClick={handleRefresh}>Try Again</button>
      </div>
    );
  }

  return (
    <section className="games-section">
      <header className="section-header">
        <h2>Today's NBA Games</h2>
        <p className="update-info">
          Updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'N/A'}
          <button onClick={handleRefresh} className="refresh-btn">↻ Refresh</button>
        </p>
      </header>

      {games.length > 0 ? (
        <div className="games-grid">
          {games.map((game, i) => (
            <div 
              key={i} 
              className={`game-card ${game.is_live ? 'live-pulse' : game.is_completed ? 'completed' : ''}`}
            >
              <div className="matchup">
                {game.away_team} @ {game.home_team}
              </div>
              <div className="score">
                {game.score !== 'N/A' ? game.score : game.status}
              </div>
              {game.is_live && (
                <div className="live-info">
                  Q{game.quarter} • {game.time_remaining}
                </div>
              )}
              {game.is_completed && (
                <div className="completed-info">Final</div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="no-games">No games scheduled today</p>
      )}
    </section>
  );
}

export default NBAGamesTicker;