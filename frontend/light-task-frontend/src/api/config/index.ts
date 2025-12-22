import { LightTaskClient } from '../client';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = new LightTaskClient({
  BASE: API_BASE_URL,
  TOKEN: async (): Promise<string> => {
    const token = localStorage.getItem('accessToken');
    return token || '';
  },
});