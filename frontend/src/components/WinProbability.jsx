// src/components/WinProbability.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

const BULLS_DATA_URL = 'https://raw.githubusercontent.com/rtjohnson0/ChicagoBullsDashboard/main/bulls_daily.json';

function WinProbability() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(BULLS_DATA_URL);
      setData(res.data);
      console.log('Win prob data loaded:', res.data);
    } catch (err) {
      setError('Failed to load win probability');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();

    // Auto-refresh every 60 seconds (same as other components)
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => fetchData();

  if (loading && !data) {
    return <div className="loading">Loading win probability...</div>;
  }

  if (error) {
    return (
      <div className="error-message">
        {error}
        <button onClick={handleRefresh}>Retry</button>
      </div>
    );
  }

  const winProb = data?.win_probability ?? 50;
  const explanation = data?.win_explanation ?? "Based on net rating, home advantage, and recent form";

  return (
    <div className="win-prob-section">
      <div className="header">
        <h2>Next Game Win Probability</h2>
        <button onClick={handleRefresh} className="refresh-btn">↻ Refresh</button>
      </div>

      <div className="gauge-container">
        <CircularProgressbar
          value={winProb}
          text={`${winProb}%`}
          styles={buildStyles({
            pathColor: winProb > 55 ? '#CE1141' : '#ef4444',
            textColor: '#fff',
            trailColor: 'rgba(255,255,255,0.1)',
          })}
        />
      </div>

      <p className="explanation">{explanation}</p>

      <p className="next-opponent">
        vs {data?.next_game?.opponent || 'TBD'} 
        ({data?.next_game?.is_home ? 'Home' : 'Away'})
      </p>
    </div>
  );
}

export default WinProbability;