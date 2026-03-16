import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import './App.css';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // REPLACE WITH YOUR ACTUAL RAW GITHUB URL
        const response = await axios.get(
          'https://raw.githubusercontent.com/rtjohnson0/ChicagoBullsDashboard/main/bulls_team_efficiency.json'
        );
        setData(response.data);
      } catch (err) {
        setError('Failed to load Bulls data. Please try again later.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-black">
        <div className="text-3xl text-bullsRed animate-pulse">Loading Bulls Dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-black">
        <div className="text-xl text-red-400 bg-gray-900/50 p-6 rounded-xl">{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-black">
        <div className="text-xl text-gray-400">No data available</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-black to-gray-900 text-white">
      <div className="app-container">
        {/* Header */}
        <header className="header">
          <h1>Chicago Bulls Daily Efficiency Dashboard</h1>
          <p className="update-date">Updated: {data.date}</p>
        </header>

        {/* Win Probability */}
        {data.next_game && (
          <section className="win-prob-section">
            <h2>Next Game Win Probability</h2>
            <div className="gauge-container">
              <CircularProgressbar
                value={data.win_prob || 50}
                text={`${data.win_prob || 'N/A'}%`}
                styles={buildStyles({
                  pathColor: data.win_prob > 50 ? '#CE1141' : '#ef4444',
                  textColor: '#ffffff',
                  trailColor: 'rgba(255,255,255,0.08)',
                })}
                aria-label={`Estimated win probability: ${data.win_prob || 'N/A'}% against ${data.next_game.opponent}`}
              />
            </div>
            <p className="next-game-info">
              vs {data.next_game.opponent} • {data.next_game.is_home ? 'Home' : 'Away'}
            </p>
          </section>
        )}

        {/* Advanced Stats Grid */}
        <section className="stats-grid">
          <div className="stat-card">
            <h3>Offensive Rating</h3>
            <p>{data.bulls_advanced?.off_rating?.toFixed(1) || 'N/A'}</p>
          </div>
          <div className="stat-card">
            <h3>Defensive Rating</h3>
            <p>{data.bulls_advanced?.def_rating?.toFixed(1) || 'N/A'}</p>
          </div>
          <div className="stat-card">
            <h3>Net Rating</h3>
            <p className={data.bulls_advanced?.net_rating > 0 ? 'positive' : 'negative'}>
              {data.bulls_advanced?.net_rating?.toFixed(1) || 'N/A'}
            </p>
          </div>
          <div className="stat-card">
            <h3>True Shooting %</h3>
            <p>{(data.bulls_advanced?.ts_pct * 100)?.toFixed(1) || 'N/A'}%</p>
          </div>
          <div className="stat-card">
            <h3>Pace</h3>
            <p>{data.bulls_advanced?.pace?.toFixed(1) || 'N/A'}</p>
          </div>
        </section>

        {/* Injuries */}
        {data.injuries?.length > 0 && (
          <section className="injuries-section">
            <h2>Current Injuries</h2>
            <div className="overflow-x-auto">
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

        <section className="mb-16">
  <h2 className="text-2xl font-semibold mb-6 text-center text-gray-200">Live NBA Games Today</h2>
  
  {data.all_games_today?.length > 0 ? (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {data.all_games_today.map((game, i) => (
        <div
          key={i}
          className={`glass-card p-6 text-center ${
            data.bulls_game_today && (game.away_team === 'Chicago Bulls' || game.home_team === 'Chicago Bulls')
              ? 'border-bullsRed border-2 animate-pulse'
              : ''
          }`}
        >
          <p className="text-xl font-bold">
            {game.away_team} @ {game.home_team}
          </p>
          <p className="text-lg mt-2">
            {game.is_live ? (
              <span className="text-neonRed font-semibold animate-pulse">LIVE - {game.score}</span>
            ) : (
              game.status
            )}
          </p>
        </div>
      ))}
    </div>
  ) : (
    <p className="text-center text-gray-400">No games scheduled today</p>
  )}
</section>

        {/* Next Game */}
        {data.next_game && (
          <section className="next-game-section">
            <h2>Next Game</h2>
            <div className="glass-card">
              <p><strong>Date:</strong> {data.next_game.date}</p>
              <p><strong>Opponent:</strong> {data.next_game.opponent}</p>
              <p><strong>Location:</strong> {data.next_game.is_home ? 'Home' : 'Away'}</p>
            </div>
          </section>
        )}
      </div>

      <footer className="footer">
        <p>Data from NBA API • Daily auto-update via GitHub Actions</p>
      </footer>
    </div>
  );
}

export default App;