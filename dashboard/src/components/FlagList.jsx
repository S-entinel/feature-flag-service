import React from 'react';
import FlagCard from './FlagCard';

const FlagList = ({ flags, onEdit, onDelete, onToggle, loading }) => {
  if (loading) {
    return (
      <div className="flag-list-loading">
        <div className="spinner"></div>
        <p>Loading flags...</p>
      </div>
    );
  }

  if (!flags || flags.length === 0) {
    return (
      <div className="flag-list-empty">
        <div className="empty-state">
          <div className="empty-icon">🚩</div>
          <h3>No Feature Flags Yet</h3>
          <p>Create your first feature flag to get started!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flag-list">
      <div className="flag-list-header">
        <h2>Feature Flags ({flags.length})</h2>
      </div>
      <div className="flag-grid">
        {flags.map((flag) => (
          <FlagCard
            key={flag.key}
            flag={flag}
            onEdit={onEdit}
            onDelete={onDelete}
            onToggle={onToggle}
          />
        ))}
      </div>
    </div>
  );
};

export default FlagList;