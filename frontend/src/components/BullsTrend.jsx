// src/components/BullsTrends.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './BullsTrends.css';

const BULLS_URL = 'https://raw.githubusercontent.com/rtjohnson0/ChicagoBullsDashboard/main/bulls_daily.json';

function BullsTrends() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const res = await axios.get(BULLS_URL);
        setData(res.data);
      } catch (err) {
        setError('Failed to load trends');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) return <div className="loading">Loading trends...</div>;
  if (error) return <div className="error">{error}</div>;

  const season = data?.bulls_season_stats || {};
  const last5 = data?.last5_averages || {};
  const ranks = data?.league_ranks || {};

  const getTrend = (seasonVal, last5Val) => {
    if (!seasonVal || !last5Val) return '—';
    const diff = last5Val - seasonVal;
    if (Math.abs(diff) < 0.5) return '—';
    return diff > 0 ? '↑' : '↓';
  };

  const getTrendColor = (seasonVal, last5Val) => {
    if (!seasonVal || !last5Val) return 'gray';
    return last5Val > seasonVal ? 'green' : 'red';
  };

  return (
    <section className="trends-section">
      <h2>Trends & League Ranks</h2>

      <div className="trends-grid">
        <div className="trend-card">
          <h3>PPG</h3>
          <p className="value">{season.ppg?.toFixed(1) || 'N/A'}</p>
          <p className="rank">League: {ranks.pts ? `${ranks.pts}${ranks.pts === 1 ? 'st' : ranks.pts === 2 ? 'nd' : ranks.pts === 3 ? 'rd' : 'th'}` : 'N/A'}</p>
          <span className={`trend-arrow ${getTrendColor(season.ppg, last5.ppg)}`}>
            {getTrend(season.ppg, last5.ppg)}
          </span>
        </div>

        <div className="trend-card">
          <h3>RPG</h3>
          <p className="value">{season.rpg?.toFixed(1) || 'N/A'}</p>
          <p className="rank">League: {ranks.reb ? `${ranks.reb}${ranks.reb === 1 ? 'st' : ranks.reb === 2 ? 'nd' : ranks.reb === 3 ? 'rd' : 'th'}` : 'N/A'}</p>
          <span className={`trend-arrow ${getTrendColor(season.rpg, last5.rpg)}`}>
            {getTrend(season.rpg, last5.rpg)}
          </span>
        </div>

        <div className="trend-card">
          <h3>APG</h3>
          <p className="value">{season.apg?.toFixed(1) || 'N/A'}</p>
          <p className="rank">League: {ranks.ast ? `${ranks.ast}${ranks.ast === 1 ? 'st' : ranks.ast === 2 ? 'nd' : ranks.ast === 3 ? 'rd' : 'th'}` : 'N/A'}</p>
          <span className={`trend-arrow ${getTrendColor(season.apg, last5.apg)}`}>
            {getTrend(season.apg, last5.apg)}
          </span>
        </div>

        {/* Add more stats as needed */}
      </div>
    </section>
  );
}

export default BullsTrends;