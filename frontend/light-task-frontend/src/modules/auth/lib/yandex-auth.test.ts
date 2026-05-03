import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  buildYandexAuthUrl,
  getSafeInternalPath,
  getYandexNextPath,
  redirectToYandexAuth,
} from './yandex-auth';

describe('yandex-auth helpers', () => {
  beforeEach(() => {
    sessionStorage.clear();
  });

  it('builds auth url with projects as default next path', () => {
    expect(buildYandexAuthUrl()).toBe('/api/auth/yandex/start?next=%2Fprojects');
  });

  it('continues pending invite flow', () => {
    sessionStorage.setItem('pendingInviteToken', 'invite-token');

    expect(getYandexNextPath()).toBe('/invite/invite-token');
    expect(buildYandexAuthUrl()).toBe(
      '/api/auth/yandex/start?next=%2Finvite%2Finvite-token',
    );
  });

  it('rejects external next paths', () => {
    expect(getSafeInternalPath('https://example.com')).toBe('/projects');
    expect(getSafeInternalPath('//example.com')).toBe('/projects');
  });

  it('uses full page redirect for Yandex auth', () => {
    const assign = vi.fn();
    const originalLocation = window.location;

    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...originalLocation, assign },
    });

    redirectToYandexAuth();

    expect(assign).toHaveBeenCalledWith('/api/auth/yandex/start?next=%2Fprojects');

    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
  });
});
