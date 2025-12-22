import React, { useState, useEffect } from 'react';
import { cacheApi } from '../services/api';

const CacheStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);

  const fetchStats = async () => {
    try {
      const data = await cacheApi.getStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch cache stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClearCache = async () => {
    if (!window.confirm('Are you sure you want to clear the cache?')) {
      return;
    }

    setClearing(true);
    try {
      await cacheApi.clear();
      await fetchStats();
      alert('Cache cleared successfully!');
    } catch (err) {
      alert('Failed to clear cache');
    } finally {
      setClearing(false);
    }
  };

  useEffect(() => {
    fetchStats();
    // Refresh stats every 10 seconds
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="cache-stats loading">Loading cache stats...</div>;
  }

  if (!stats || !stats.enabled) {
    return (
      <div className="cache-stats disabled">
        <h3>⚠️ Cache Disabled</h3>
        <p>Redis cache is not available. Service is running without caching.</p>
      </div>
    );
  }

  const hitRate = stats.hit_rate || 0;

  return (
    <div className="cache-stats">
      <div className="cache-header">
        <h3>📊 Cache Statistics</h3>
        <button
          className="btn btn-small btn-secondary"
          onClick={handleClearCache}
          disabled={clearing}
        >
          {clearing ? 'Clearing...' : 'Clear Cache'}
        </button>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.flag_keys || 0}</div>
          <div className="stat-label">Cached Keys</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{stats.keyspace_hits || 0}</div>
          <div className="stat-label">Cache Hits</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{stats.keyspace_misses || 0}</div>
          <div className="stat-label">Cache Misses</div>
        </div>

        <div className="stat-card">
          <div className="stat-value">{hitRate.toFixed(1)}%</div>
          <div className="stat-label">Hit Rate</div>
          <div className="stat-progress">
            <div
              className="stat-progress-bar"
              style={{ width: `${hitRate}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="cache-info">
        <p className="cache-status">
          ✅ Redis cache is <strong>enabled</strong> and operational
        </p>
      </div>
    </div>
  );
};

export default CacheStats;