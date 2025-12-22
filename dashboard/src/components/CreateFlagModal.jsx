import React, { useState } from 'react';

const CreateFlagModal = ({ isOpen, onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    key: '',
    name: '',
    description: '',
    enabled: false,
    rollout_percentage: 100,
  });

  const [error, setError] = useState('');

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
    if (!formData.key.trim()) {
      setError('Key is required');
      return;
    }
    if (!formData.name.trim()) {
      setError('Name is required');
      return;
    }
    if (formData.rollout_percentage < 0 || formData.rollout_percentage > 100) {
      setError('Rollout percentage must be between 0 and 100');
      return;
    }

    try {
      await onCreate({
        ...formData,
        rollout_percentage: parseFloat(formData.rollout_percentage),
      });
      
      // Reset form
      setFormData({
        key: '',
        name: '',
        description: '',
        enabled: false,
        rollout_percentage: 100,
      });
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create flag');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create New Flag</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}

          <div className="form-group">
            <label htmlFor="key">
              Key <span className="required">*</span>
            </label>
            <input
              type="text"
              id="key"
              name="key"
              value={formData.key}
              onChange={handleChange}
              placeholder="e.g., new_checkout_flow"
              required
            />
            <small className="form-hint">
              Unique identifier (lowercase, underscores allowed)
            </small>
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
              placeholder="e.g., New Checkout Flow"
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
            <input
              type="number"
              id="rollout_percentage"
              name="rollout_percentage"
              value={formData.rollout_percentage}
              onChange={handleChange}
              min="0"
              max="100"
              step="0.1"
            />
            <small className="form-hint">
              Percentage of users who will see this feature (0-100)
            </small>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="enabled"
                checked={formData.enabled}
                onChange={handleChange}
              />
              <span>Enable flag immediately</span>
            </label>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create Flag
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateFlagModal;