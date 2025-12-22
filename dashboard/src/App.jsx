import React, { useState, useEffect } from 'react';
import FlagList from './components/FlagList';
import CreateFlagModal from './components/CreateFlagModal';
import EditFlagModal from './components/EditFlagModal';
import CacheStats from './components/CacheStats';
import { flagsApi } from './services/api';
import './App.css';

function App() {
  const [flags, setFlags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedFlag, setSelectedFlag] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch all flags
  const fetchFlags = async () => {
    setLoading(true);
    try {
      const data = await flagsApi.getAll();
      setFlags(data);
    } catch (err) {
      console.error('Failed to fetch flags:', err);
      alert('Failed to load flags. Make sure the API is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFlags();
  }, []);

  // Create flag
  const handleCreate = async (flagData) => {
    await flagsApi.create(flagData);
    await fetchFlags();
  };

  // Update flag
  const handleUpdate = async (key, flagData) => {
    await flagsApi.update(key, flagData);
    await fetchFlags();
  };

  // Delete flag
  const handleDelete = async (key) => {
    if (!window.confirm(`Are you sure you want to delete flag "${key}"?`)) {
      return;
    }

    try {
      await flagsApi.delete(key);
      await fetchFlags();
    } catch (err) {
      alert('Failed to delete flag');
    }
  };

  // Toggle flag enabled state
  const handleToggle = async (key, enabled) => {
    try {
      await flagsApi.update(key, { enabled });
      await fetchFlags();
    } catch (err) {
      alert('Failed to toggle flag');
    }
  };

  // Open edit modal
  const handleEdit = (flag) => {
    setSelectedFlag(flag);
    setEditModalOpen(true);
  };

  // Filter flags by search query
  const filteredFlags = flags.filter((flag) => {
    const query = searchQuery.toLowerCase();
    return (
      flag.key.toLowerCase().includes(query) ||
      flag.name.toLowerCase().includes(query) ||
      (flag.description && flag.description.toLowerCase().includes(query))
    );
  });

  // Calculate statistics
  const enabledCount = flags.filter((f) => f.enabled).length;
  const disabledCount = flags.length - enabledCount;

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="header-left">
            <h1>🚩 Feature Flag Dashboard</h1>
            <p className="header-subtitle">
              Manage feature flags and rollouts
            </p>
          </div>
          <div className="header-right">
            <button
              className="btn btn-primary"
              onClick={() => setCreateModalOpen(true)}
            >
              + Create Flag
            </button>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          {/* Statistics */}
          <div className="stats-bar">
            <div className="stat-item">
              <span className="stat-number">{flags.length}</span>
              <span className="stat-text">Total Flags</span>
            </div>
            <div className="stat-item enabled">
              <span className="stat-number">{enabledCount}</span>
              <span className="stat-text">Enabled</span>
            </div>
            <div className="stat-item disabled">
              <span className="stat-number">{disabledCount}</span>
              <span className="stat-text">Disabled</span>
            </div>
          </div>

          {/* Search */}
          <div className="search-bar">
            <input
              type="text"
              className="search-input"
              placeholder="🔍 Search flags by key, name, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Cache Stats */}
          <CacheStats />

          {/* Flags List */}
          <FlagList
            flags={filteredFlags}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onToggle={handleToggle}
            loading={loading}
          />
        </div>
      </main>

      {/* Modals */}
      <CreateFlagModal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreate={handleCreate}
      />

      <EditFlagModal
        isOpen={editModalOpen}
        onClose={() => {
          setEditModalOpen(false);
          setSelectedFlag(null);
        }}
        onUpdate={handleUpdate}
        flag={selectedFlag}
      />

      <footer className="app-footer">
        <p>
          Feature Flag Service v1.0.0 | Built with React
        </p>
      </footer>
    </div>
  );
}

export default App;