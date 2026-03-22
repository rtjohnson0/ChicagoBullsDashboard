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
    } catch (err) {
      setError('Failed to load today\'s NBA games.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGames();
    const interval = setInterval(fetchGames, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => fetchGames();

  if (loading && games.length === 0) return <div className="loading">Loading today's NBA games...</div>;
  if (error) return <div className="error-message">{error} <button onClick={handleRefresh}>Retry</button></div>;

  return (
    <section className="games-section">
      <header className="games-header">
        <h2>Today's NBA Games</h2>
        <div className="update-bar">
          <span>Updated: {lastUpdated ? lastUpdated.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'N/A'}</span>
          <button onClick={handleRefresh} className="refresh-btn">↻ Refresh</button>
        </div>
      </header>

      {games.length > 0 ? (
        <div className="games-grid">
          {games.map((game, i) => {
            const isLive = game.is_live;
            const isFinal = game.is_completed;

            return (
              <div 
                key={i} 
                className={`game-card ${isLive ? 'live' : isFinal ? 'final' : 'scheduled'}`}
              >
                <div className="matchup">
                  {game.away_team} @ {game.home_team}
                </div>

                <div className="score-display">
                  <div className="score">
                    {game.score !== 'N/A' ? game.score : '—'}
                  </div>

                  <div className={`status-badge ${isLive ? 'live-badge' : isFinal ? 'final-badge' : 'scheduled-badge'}`}>
                    {isFinal ? 'FINAL' : game.status}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="no-games">No games scheduled today</p>
      )}
    </section>
  );
}

export default NBAGamesTicker;