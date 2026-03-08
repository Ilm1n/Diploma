import type { Router } from 'vue-router';

import { onConsentChanged } from '@/shared/consent/consent';
import { ensureAnalyticsState, trackPageView } from '@/shared/analytics/yandex';

let bootstrapped = false;

export function bootstrapAnalytics(router: Router): void {
  if (bootstrapped) return;
  bootstrapped = true;

  void ensureAnalyticsState().then(() => {
    trackPageView(window.location.pathname + window.location.search);
  });

  onConsentChanged(() => {
    void ensureAnalyticsState().then(() => {
      trackPageView(window.location.pathname + window.location.search);
    });
  });

  router.afterEach((to) => {
    void ensureAnalyticsState().then(() => {
      trackPageView(to.fullPath);
    });
  });
}
