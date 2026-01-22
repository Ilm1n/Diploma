// src/modules/auth/store/auth.store.ts
import {defineStore} from 'pinia';
import {ref, computed} from 'vue';
import {apiClient} from '@/api/config';
import type {
  UserRead,
  Body_login_for_access_token_api_auth_login_post,
  UserCreate,
  UserUpdate,
} from '@/api/client';
import {useRouter} from 'vue-router';

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter();

  const accessToken = ref<string | null>(localStorage.getItem('accessToken'));
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'));
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
        setTokens(response.accessToken, response.refreshToken);
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

  async function register(payload: UserCreate) {
    isLoading.value = true;
    try {
      await apiClient.users.createUserApiUsersRegisterPost(payload);
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
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


  async function updateProfile(payload: UserUpdate) {
    isLoading.value = true;
    try {
      const updatedUser = await apiClient.users.updateUserMeApiUsersMePatch(payload);
      user.value = updatedUser;
    } catch (error) {
      console.error('Failed to update profile:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function uploadAvatar(file: File) {
    isLoading.value = true;
    try {
      const updatedUser = await apiClient.users.uploadAvatarApiUsersMeAvatarPost({
        file: file
      });
      user.value = updatedUser;
    } catch (error) {
      console.error('Failed to upload avatar:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  function logout() {
    accessToken.value = null;
    user.value = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    router.push('/login');
  }

  function setTokens(access: string, refresh: string) {
    accessToken.value = access;
    refreshToken.value = refresh;
    localStorage.setItem('accessToken', access);
    localStorage.setItem('refreshToken', refresh);
  }

  return {
    accessToken,
    refreshToken,
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser,
    initAuth,
    setTokens,
    updateProfile,
    uploadAvatar,
  };
});