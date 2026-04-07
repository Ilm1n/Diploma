export type TrustedReplayContextOptions = {
  referrer?: string;
  inIframe?: boolean;
};

export type AnalyticsRuntimeOptions = {
  environmentEnabled: boolean;
  storedConsentGranted: boolean;
  trustedReplayContext: boolean;
};

export type CookieBannerVisibilityOptions = {
  hasStoredDecision: boolean;
  trustedReplayContext: boolean;
};

const TRUSTED_YANDEX_REPLAY_HOST_PATTERN =
  /(^|\.)webvisor\.com$|(^|\.)metri[ck]a\.yandex\.(ru|com|by|com\.tr)$/i;

function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}

function isEmbeddedInIframe(): boolean {
  if (!isBrowser()) return false;

  try {
    return window.self !== window.top;
  } catch {
    return true;
  }
}

export function isTrustedYandexReplayHost(hostname: string): boolean {
  return TRUSTED_YANDEX_REPLAY_HOST_PATTERN.test(hostname.trim().toLowerCase());
}

export function isTrustedYandexReplayContext(
  options: TrustedReplayContextOptions = {},
): boolean {
  const inIframe = options.inIframe ?? isEmbeddedInIframe();
  if (!inIframe) return false;

  const referrer = options.referrer ?? (isBrowser() ? document.referrer : '');
  if (!referrer) return false;

  try {
    return isTrustedYandexReplayHost(new URL(referrer).hostname);
  } catch {
    return false;
  }
}

export function isAnalyticsRuntimeAllowed(
  options: AnalyticsRuntimeOptions,
): boolean {
  return (
    options.environmentEnabled &&
    (options.storedConsentGranted || options.trustedReplayContext)
  );
}

export function shouldShowCookieBanner(
  options: CookieBannerVisibilityOptions,
): boolean {
  return !options.hasStoredDecision && !options.trustedReplayContext;
}
