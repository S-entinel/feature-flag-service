import React, { useState, useEffect } from 'react';

const EditFlagModal = ({ isOpen, onClose, onUpdate, flag }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    enabled: false,
    rollout_percentage: 100,
  });

  const [error, setError] = useState('');

  useEffect(() => {
    if (flag) {
      setFormData({
        name: flag.name,
        description: flag.description || '',
        enabled: flag.enabled,
        rollout_percentage: flag.rollout_percentage,
      });
    }
  }, [flag]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validation
    if (!formData.name.trim()) {
      setError('Name is required');
      return;
    }
    if (formData.rollout_percentage < 0 || formData.rollout_percentage > 100) {
      setError('Rollout percentage must be between 0 and 100');
      return;
    }

    try {
      await onUpdate(flag.key, {
        ...formData,
        rollout_percentage: parseFloat(formData.rollout_percentage),
      });
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update flag');
    }
  };

  if (!isOpen || !flag) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit Flag</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label>Key</label>
            <input
              type="text"
              value={flag.key}
              disabled
              className="input-disabled"
            />
            <small className="form-hint">Key cannot be changed</small>
          </div>

          <div className="form-group">
            <label htmlFor="name">
              Name <span className="required">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Optional description..."
              rows="3"
            />
          </div>

          <div className="form-group">
            <label htmlFor="rollout_percentage">
              Rollout Percentage
            </label>
            <div className="percentage-input-group">
              <input
                type="range"
                id="rollout_percentage"
                name="rollout_percentage"
                value={formData.rollout_percentage}
                onChange={handleChange}
                min="0"
                max="100"
                step="1"
                className="range-slider"
              />
              <input
                type="number"
                name="rollout_percentage"
                value={formData.rollout_percentage}
                onChange={handleChange}
                min="0"
                max="100"
                step="0.1"
                className="percentage-input"
              />
              <span className="percentage-label">%</span>
            </div>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="enabled"
                checked={formData.enabled}
                onChange={handleChange}
              />
              <span>Flag enabled</span>
            </label>
          </div>

          <div className="flag-info">
            <div className="info-item">
              <span className="info-label">Created:</span>
              <span className="info-value">
                {new Date(flag.created_at).toLocaleString()}
              </span>
            </div>
            <div className="info-item">
              <span className="info-label">Last Updated:</span>
              <span className="info-value">
                {new Date(flag.updated_at).toLocaleString()}
              </span>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Update Flag
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditFlagModal;