import { KantanoClient } from '../client';
import { AuthorizedHttpRequest } from './AuthorizedHttpRequest';
import { API_BASE_URL } from './axios-instance';
import { getAccessToken } from '@/modules/auth/lib/access-token';

export const apiClient = new KantanoClient(
  {
    BASE: API_BASE_URL,
    TOKEN: async () => getAccessToken() ?? '',
  },
  AuthorizedHttpRequest
);
