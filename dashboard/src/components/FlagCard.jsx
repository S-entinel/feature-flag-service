import React from 'react';

const FlagCard = ({ flag, onEdit, onDelete, onToggle }) => {
  const handleToggle = async () => {
    await onToggle(flag.key, !flag.enabled);
  };

  return (
    <div className="flag-card">
      <div className="flag-header">
        <div className="flag-title-section">
          <h3 className="flag-key">{flag.key}</h3>
          <p className="flag-name">{flag.name}</p>
        </div>
        <div className="flag-status">
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={flag.enabled}
              onChange={handleToggle}
            />
            <span className="toggle-slider"></span>
          </label>
          <span className={`status-badge ${flag.enabled ? 'enabled' : 'disabled'}`}>
            {flag.enabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>
      </div>

      {flag.description && (
        <p className="flag-description">{flag.description}</p>
      )}

      <div className="flag-details">
        <div className="detail-item">
          <span className="detail-label">Rollout:</span>
          <span className="detail-value">{flag.rollout_percentage}%</span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Created:</span>
          <span className="detail-value">
            {new Date(flag.created_at).toLocaleDateString()}
          </span>
        </div>
        <div className="detail-item">
          <span className="detail-label">Updated:</span>
          <span className="detail-value">
            {new Date(flag.updated_at).toLocaleDateString()}
          </span>
        </div>
      </div>

      <div className="flag-actions">
        <button
          className="btn btn-secondary"
          onClick={() => onEdit(flag)}
        >
          Edit
        </button>
        <button
          className="btn btn-danger"
          onClick={() => onDelete(flag.key)}
        >
          Delete
        </button>
      </div>
    </div>
  );
};

export default FlagCard;