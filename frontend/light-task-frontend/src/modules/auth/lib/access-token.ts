import { ref } from 'vue';

export const accessTokenState = ref<string | null>(null);

export function getAccessToken(): string | null {
  return accessTokenState.value;
}

export function setAccessTokenValue(token: string | null): void {
  accessTokenState.value = token;
}
