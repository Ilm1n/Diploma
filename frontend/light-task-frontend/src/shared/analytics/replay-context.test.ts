import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  isAnalyticsRuntimeAllowed,
  isTrustedYandexReplayContext,
  shouldShowCookieBanner,
} from './replay-context';

const CONSENT_STORAGE_KEY = 'kantano-cookie-consent-v1';

describe('isTrustedYandexReplayContext', () => {
  it('returns false for top-level visits without iframe context', () => {
    expect(
      isTrustedYandexReplayContext({
        referrer: 'https://metrika.yandex.ru/inpage/click_map',
        inIframe: false,
      }),
    ).toBe(false);
  });

  it('returns true for trusted Yandex replay iframe referrers', () => {
    expect(
      isTrustedYandexReplayContext({
        referrer: 'https://metrika.yandex.ru/inpage/link_map?url=https%3A%2F%2Fkantano.ru',
        inIframe: true,
      }),
    ).toBe(true);

    expect(
      isTrustedYandexReplayContext({
        referrer: 'https://webvisor.com/app?foo=bar',
        inIframe: true,
      }),
    ).toBe(true);
  });

  it('returns false for untrusted or invalid iframe referrers', () => {
    expect(
      isTrustedYandexReplayContext({
        referrer: 'https://example.com/embed',
        inIframe: true,
      }),
    ).toBe(false);

    expect(
      isTrustedYandexReplayContext({
        referrer: 'not-a-valid-url',
        inIframe: true,
      }),
    ).toBe(false);
  });
});

describe('analytics permission helpers', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it('keeps analytics disabled for normal visitors without consent', () => {
    expect(
      isAnalyticsRuntimeAllowed({
        environmentEnabled: true,
        storedConsentGranted: false,
        trustedReplayContext: false,
      }),
    ).toBe(false);
  });

  it('enables analytics inside trusted replay iframe without stored consent', () => {
    expect(
      isAnalyticsRuntimeAllowed({
        environmentEnabled: true,
        storedConsentGranted: false,
        trustedReplayContext: true,
      }),
    ).toBe(true);
  });

  it('preserves current behavior for normal visitors with stored consent', () => {
    expect(
      isAnalyticsRuntimeAllowed({
        environmentEnabled: true,
        storedConsentGranted: true,
        trustedReplayContext: false,
      }),
    ).toBe(true);
  });

  it('hides the cookie banner inside trusted replay iframe without a stored decision', () => {
    expect(
      shouldShowCookieBanner({
        hasStoredDecision: false,
        trustedReplayContext: true,
      }),
    ).toBe(false);
  });

  it('shows the cookie banner for normal visitors without a stored decision', () => {
    expect(
      shouldShowCookieBanner({
        hasStoredDecision: false,
        trustedReplayContext: false,
      }),
    ).toBe(true);
  });

  it('does not persist consent when analytics is enabled only for replay iframe rendering', () => {
    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');

    const isAllowed = isAnalyticsRuntimeAllowed({
      environmentEnabled: true,
      storedConsentGranted: false,
      trustedReplayContext: true,
    });

    expect(isAllowed).toBe(true);
    expect(window.localStorage.getItem(CONSENT_STORAGE_KEY)).toBeNull();
    expect(setItemSpy).not.toHaveBeenCalled();
  });
});
