// src/modules/auth/store/auth.store.ts
import {defineStore} from 'pinia';
import {computed, ref} from 'vue';
import {apiClient} from '@/api/config';
import type {Body_login_for_access_token_api_auth_login_post, UserCreate, UserRead, UserUpdate,} from '@/api/client';
import {useRouter} from 'vue-router';

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
      }
    }
  }

  async function login(credentials: Body_login_for_access_token_api_auth_login_post) {
    isLoading.value = true;
    try {
      const response = await apiClient.auth.loginForAccessTokenApiAuthLoginPost(credentials);

      if (response.accessToken) {
        setAccessToken(response.accessToken);
        await fetchUser();

        const pendingInvite = sessionStorage.getItem('pendingInviteToken');
        if (pendingInvite) {
          sessionStorage.removeItem('pendingInviteToken');
          await router.push(`/invite/${pendingInvite}`);
          return true;
        }

        await router.push('/projects');
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
      // Проверь имя метода после генерации
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
      user.value = await apiClient.users.readUsersMeApiUsersMeGet();
    } catch (error) {
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function updateProfile(payload: UserUpdate) {
    isLoading.value = true;
    try {
      user.value = await apiClient.users.updateUserMeApiUsersMePatch(payload);
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
      user.value = await apiClient.users.uploadAvatarApiUsersMeAvatarPost({
        file: file
      });
    } catch (error) {
      console.error('Failed to upload avatar:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteAvatar(): Promise<void> {
    isLoading.value = true;
    try {
      user.value = await apiClient.users.deleteAvatarApiUsersMeAvatarDelete();
    } catch (error) {
      console.error('Failed to delete avatar:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function logout() {
    try {
      await apiClient.auth.logoutApiAuthLogoutPost();
    } catch (e) {
      console.warn('Logout request failed', e);
    } finally {
      accessToken.value = null;
      user.value = null;
      localStorage.removeItem('accessToken');
      await router.push('/login');
    }
  }

  function setAccessToken(access: string) {
    accessToken.value = access;
    localStorage.setItem('accessToken', access);
  }

  return {
    accessToken,
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser,
    initAuth,
    setAccessToken,
    updateProfile,
    uploadAvatar,
    deleteAvatar,
  };
});