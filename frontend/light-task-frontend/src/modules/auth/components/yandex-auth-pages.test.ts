import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import LoginPage from './LoginPage.vue';
import RegisterPage from './RegisterPage.vue';
import YandexCallbackPage from './YandexCallbackPage.vue';

const mocks = vi.hoisted(() => ({
  restoreSession: vi.fn(),
  routerPush: vi.fn(),
  routerReplace: vi.fn(),
  routeQuery: {} as Record<string, unknown>,
  toastAdd: vi.fn(),
}));

vi.mock('@/modules/auth/store/auth.store', () => ({
  useAuthStore: () => ({
    login: vi.fn(),
    register: vi.fn(),
    restoreSession: mocks.restoreSession,
  }),
}));

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: mocks.routeQuery }),
  useRouter: () => ({
    push: mocks.routerPush,
    replace: mocks.routerReplace,
  }),
}));

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({ add: mocks.toastAdd }),
}));

vi.mock('@unhead/vue', () => ({
  useHead: vi.fn(),
}));

vi.mock('@/composables/useTheme', () => ({
  useTheme: () => ({
    isDark: false,
    toggleTheme: vi.fn(),
  }),
}));

const globalOptions = {
  global: {
    stubs: {
      RouterLink: {
        template: '<a><slot /></a>',
      },
      InputText: {
        template: '<input />',
      },
      Password: {
        template: '<input />',
      },
      Button: {
        props: ['label'],
        template: '<button>{{ label }}</button>',
      },
      ProgressSpinner: {
        template: '<div />',
      },
    },
  },
};

describe('Yandex auth pages', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.routeQuery = {};
    sessionStorage.clear();
  });

  it('shows Yandex button on login page', () => {
    const wrapper = mount(LoginPage, globalOptions);

    expect(wrapper.text()).toContain('Войти через Yandex');
  });

  it('shows Yandex button on register page', () => {
    const wrapper = mount(RegisterPage, globalOptions);

    expect(wrapper.text()).toContain('Войти через Yandex');
  });

  it('restores session and redirects to callback next path', async () => {
    mocks.restoreSession.mockResolvedValue(true);
    mocks.routeQuery = { next: '/invite/invite-token' };
    sessionStorage.setItem('pendingInviteToken', 'invite-token');

    mount(YandexCallbackPage, globalOptions);
    await flushPromises();

    expect(mocks.restoreSession).toHaveBeenCalledOnce();
    expect(mocks.routerReplace).toHaveBeenCalledWith('/invite/invite-token');
    expect(sessionStorage.getItem('pendingInviteToken')).toBeNull();
  });

  it('redirects to login when callback session restore fails', async () => {
    mocks.restoreSession.mockResolvedValue(false);

    mount(YandexCallbackPage, globalOptions);
    await flushPromises();

    expect(mocks.toastAdd).toHaveBeenCalled();
    expect(mocks.routerReplace).toHaveBeenCalledWith('/login');
  });
});
