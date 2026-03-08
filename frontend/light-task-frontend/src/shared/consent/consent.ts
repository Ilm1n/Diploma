export type CookieConsent = {
  necessary: true;
  analytics: boolean;
  updatedAt: string;
};

const CONSENT_STORAGE_KEY = 'kantano-cookie-consent-v1';
const CONSENT_EVENT_NAME = 'kantano:consent-changed';
const OPEN_SETTINGS_EVENT_NAME = 'kantano:open-cookie-settings';

function isBrowser(): boolean {
  return typeof window !== 'undefined';
}

function parseConsent(raw: string | null): CookieConsent | null {
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as Partial<CookieConsent>;
    if (
      parsed &&
      parsed.necessary === true &&
      typeof parsed.analytics === 'boolean' &&
      typeof parsed.updatedAt === 'string'
    ) {
      return {
        necessary: true,
        analytics: parsed.analytics,
        updatedAt: parsed.updatedAt,
      };
    }
  } catch {
    return null;
  }

  return null;
}

export function getStoredConsent(): CookieConsent | null {
  if (!isBrowser()) return null;
  return parseConsent(window.localStorage.getItem(CONSENT_STORAGE_KEY));
}

export function hasConsentDecision(): boolean {
  return getStoredConsent() !== null;
}

export function setConsent(analyticsEnabled: boolean): CookieConsent {
  const consent: CookieConsent = {
    necessary: true,
    analytics: analyticsEnabled,
    updatedAt: new Date().toISOString(),
  };

  if (isBrowser()) {
    window.localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(consent));
    window.dispatchEvent(new CustomEvent<CookieConsent>(CONSENT_EVENT_NAME, { detail: consent }));
  }

  return consent;
}

export function isAnalyticsConsentGranted(): boolean {
  return getStoredConsent()?.analytics === true;
}

export function onConsentChanged(
  callback: (consent: CookieConsent) => void,
): () => void {
  if (!isBrowser()) return () => {};

  const handler = (event: Event) => {
    const custom = event as CustomEvent<CookieConsent>;
    if (custom.detail) callback(custom.detail);
  };

  window.addEventListener(CONSENT_EVENT_NAME, handler as EventListener);
  return () => window.removeEventListener(CONSENT_EVENT_NAME, handler as EventListener);
}

export function openCookieSettings(): void {
  if (!isBrowser()) return;
  window.dispatchEvent(new Event(OPEN_SETTINGS_EVENT_NAME));
}

export function onOpenCookieSettingsRequested(
  callback: () => void,
): () => void {
  if (!isBrowser()) return () => {};

  window.addEventListener(OPEN_SETTINGS_EVENT_NAME, callback as EventListener);
  return () => window.removeEventListener(OPEN_SETTINGS_EVENT_NAME, callback as EventListener);
}
