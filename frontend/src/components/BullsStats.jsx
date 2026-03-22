// src/components/BullsStats.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './BullsStats.css';

const BULLS_URL = 'https://raw.githubusercontent.com/rtjohnson0/ChicagoBullsDashboard/main/bulls_daily.json';

function BullsStats() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(BULLS_URL);
      setData(res.data);
      setLastUpdated(new Date());
      console.log('Bulls data loaded:', res.data);
    } catch (err) {
      setError('Failed to load Bulls stats. Try refreshing.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => fetchData();

  if (loading && !data) {
    return <div className="loading">Loading Bulls stats...</div>;
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
    <section className="bulls-section">
      <header className="section-header">
        <h2>Chicago Bulls Season Stats</h2>
        <p className="update-info">
          Updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : data?.date || 'N/A'}
          <button onClick={handleRefresh} className="refresh-btn">↻ Refresh</button>
        </p>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>PPG</h3>
          <p className="stat-value">{data?.bulls_season_stats?.ppg?.toFixed(1) || 'N/A'}</p>
        </div>
        <div className="stat-card">
          <h3>RPG</h3>
          <p className="stat-value">{data?.bulls_season_stats?.rpg?.toFixed(1) || 'N/A'}</p>
        </div>
        <div className="stat-card">
          <h3>APG</h3>
          <p className="stat-value">{data?.bulls_season_stats?.apg?.toFixed(1) || 'N/A'}</p>
        </div>
        <div className="stat-card">
          <h3>Offensive Rating</h3>
          <p className="stat-value">{data?.bulls_season_stats?.off_rating?.toFixed(1) || 'N/A'}</p>
        </div>
        <div className="stat-card">
          <h3>Defensive Rating</h3>
          <p className="stat-value">{data?.bulls_season_stats?.def_rating?.toFixed(1) || 'N/A'}</p>
        </div>
        <div className="stat-card">
          <h3>Net Rating</h3>
          <p className={`stat-value ${data?.bulls_season_stats?.net_rating > 0 ? 'positive' : 'negative'}`}>
            {data?.bulls_season_stats?.net_rating?.toFixed(1) || 'N/A'}
          </p>
        </div>
        <div className="stat-card">
          <h3>True Shooting %</h3>
          <p className="stat-value">{(data?.bulls_season_stats?.ts_pct * 100)?.toFixed(1) || 'N/A'}%</p>
        </div>
        <div className="stat-card">
          <h3>Pace</h3>
          <p className="stat-value">{data?.bulls_season_stats?.pace?.toFixed(2) || 'N/A'}</p>
        </div>
      </div>

      {data?.next_game?.date && (
        <div className="next-game">
          <h3>Next Game</h3>
          <p>
            {data.next_game.date} vs {data.next_game.opponent} ({data.next_game.is_home ? 'Home' : 'Away'})
          </p>
        </div>
      )}

    {data?.injuries?.length > 0 && (
  <div className="injuries">
    <h3>Current Injuries</h3>
    <div className="injuries-grid">
      {data.injuries.map((inj, i) => {
        const statusLower = inj.status?.toLowerCase() || '';
        let statusClass = 'status-probable';
        let statusText = inj.status || 'Unknown';

        if (statusLower.includes('out')) {
          statusClass = 'status-out';
          statusText = 'Out';
        } else if (statusLower.includes('questionable') || statusLower.includes('doubtful')) {
          statusClass = 'status-questionable';
          statusText = 'Questionable';
        } else if (statusLower.includes('probable') || statusLower.includes('day-to-day')) {
          statusClass = 'status-probable';
          statusText = 'Probable';
        }

        return (
          <div key={i} className={`injury-card ${statusClass}`}>
            <div className="injury-player">{inj.player}</div>
            <div className="injury-detail">Position: {inj.position}</div>
            <div className="injury-detail">Injury: {inj.injury}</div>
            <div className={`injury-status ${statusClass}`}>
              <span className="status-dot"></span>
              {statusText}
            </div>
          </div>
        );
      })}
    </div>
  </div>
)}
    </section>
  );
}

export default BullsStats;