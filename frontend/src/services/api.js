// frontend/src/services/api.js
import axios from 'axios';

/**
 * Fetch recent workout sessions (all users).
 * We'll filter client-side by user_id.
 * @param {number} limit
 * @returns {Promise<SessionEntry[]>}
 */
export function fetchSessions(limit = 50) {
  return axios
    .get(`/api/sessions?limit=${limit}`)
    .then(res => res.data);
}

/**
 * Fetch AI-generated advice for a specific user.
 * @param {string} userId
 * @param {number} limit
 * @returns {Promise<string>}
 */
export function fetchAdvice(userId, limit = 5) {
  return axios
    .get(`/api/advice/${encodeURIComponent(userId)}?limit=${limit}`)
    .then(res => res.data.advice);
}
