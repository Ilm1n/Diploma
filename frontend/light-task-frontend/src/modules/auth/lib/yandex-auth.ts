import { API_BASE_URL } from '@/api/config/axios-instance';

const DEFAULT_AFTER_LOGIN_PATH = '/projects';

export function getSafeInternalPath(path: unknown): string {
  if (typeof path !== 'string' || !path.startsWith('/') || path.startsWith('//')) {
    return DEFAULT_AFTER_LOGIN_PATH;
  }

  return path;
}

export function getYandexNextPath(): string {
  const pendingInviteToken = sessionStorage.getItem('pendingInviteToken');
  if (pendingInviteToken) {
    return `/invite/${encodeURIComponent(pendingInviteToken)}`;
  }

  return DEFAULT_AFTER_LOGIN_PATH;
}

export function buildYandexAuthUrl(nextPath: string = getYandexNextPath()): string {
  const baseUrl = API_BASE_URL || '';
  const searchParams = new URLSearchParams({
    next: getSafeInternalPath(nextPath),
  });

  return `${baseUrl}/api/auth/yandex/start?${searchParams.toString()}`;
}

export function redirectToYandexAuth(): void {
  window.location.assign(buildYandexAuthUrl());
}
