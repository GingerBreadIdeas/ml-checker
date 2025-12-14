const BACKEND_HOST = import.meta.env.VITE_BACKEND_HOST || 'http://localhost:8000';
const API_PATH = import.meta.env.VITE_API_PATH || '/api/v1';

export const API_BASE = BACKEND_HOST;
export const API_URL = `${API_BASE}${API_PATH}`;
