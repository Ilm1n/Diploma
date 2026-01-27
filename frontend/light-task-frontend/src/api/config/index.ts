import { KantanoClient } from '../client';
import { AuthorizedHttpRequest } from './AuthorizedHttpRequest';
import { API_BASE_URL } from './axios-instance';

export const apiClient = new KantanoClient(
  {
    BASE: API_BASE_URL,
  },
  AuthorizedHttpRequest
);