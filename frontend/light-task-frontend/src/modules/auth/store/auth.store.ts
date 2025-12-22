// src/modules/auth/store/auth.store.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { apiClient } from '@/api/config';
import type { UserRead, Body_login_for_access_token_api_auth_login_post } from '@/api/client';
import { useRouter } from 'vue-router';

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter();

  const accessToken = ref<string | null>(localStorage.getItem('accessToken'));
  const user = ref<UserRead | null>(null);
  const isLoading = ref(false);

  const isAuthenticated = computed(() => !!accessToken.value);


  async function initAuth() {
    if (accessToken.value) {
      try {
        await fetchUser();
      } catch (error) {
        console.error('Token invalid or expired during init');
        logout();
      }
    }
  }

  async function login(credentials: Body_login_for_access_token_api_auth_login_post) {
    isLoading.value = true;
    try {
      const response = await apiClient.auth.loginForAccessTokenApiAuthLoginPost(credentials);

      if (response.accessToken) {
        setToken(response.accessToken);
        await fetchUser();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchUser() {
    isLoading.value = true;
    try {
      const userData = await apiClient.users.readUsersMeApiUsersMeGet();
      user.value = userData;
    } catch (error) {
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  function logout() {
    accessToken.value = null;
    user.value = null;
    localStorage.removeItem('accessToken');
    router.push('/login');
  }

  function setToken(token: string) {
    accessToken.value = token;
    localStorage.setItem('accessToken', token);
  }

  return {
    accessToken,
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    fetchUser,
    initAuth
  };
});