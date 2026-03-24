import { KantanoClient } from '../client';
import { AuthorizedHttpRequest } from './AuthorizedHttpRequest';
import { API_BASE_URL } from './axios-instance';
import { getAccessToken } from '@/modules/auth/lib/access-token';
import { currentClientMutationId } from '@/modules/realtime/lib/mutation-id';

export const apiClient = new KantanoClient(
  {
    BASE: API_BASE_URL,
    TOKEN: async () => getAccessToken() ?? '',
    HEADERS: async (): Promise<Record<string, string>> => {
      const mutationId = currentClientMutationId();
      if (mutationId) {
        return { 'X-Client-Mutation-Id': mutationId };
      }
      return {};
    },
  },
  AuthorizedHttpRequest
);
