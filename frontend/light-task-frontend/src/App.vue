<script setup lang="ts">
import { onMounted, ref } from 'vue';
import Toast from 'primevue/toast';
import { useAuthStore } from '@/modules/auth/store/auth.store';
import CookieBanner from "@/shared/ui/CookieBanner.vue";

const authStore = useAuthStore();
const isAppReady = ref(false);

onMounted(async () => {
  if (authStore.accessToken && !authStore.user) {
    try {
      await authStore.fetchUser();
    } catch (e) {
      console.error('Session restore failed:', e);
    }
  }
  setTimeout(() => {
    isAppReady.value = true;
  }, 100);
});
</script>

<template>
  <Toast />
  <ConfirmDialog />

  <Transition name="fade">
    <div v-if="!isAppReady" class="loading-overlay">
      <div class="spinner"></div>
    </div>
  </Transition>

  <router-view v-if="isAppReady" />

  <CookieBanner />
</template>

<style>
.loading-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
  background-color: #f8f9fa;
}

.dark .loading-overlay {
  background-color: #0f172a;
}

.spinner {
  width: 40px; height: 40px;
  border: 3px solid #e2e8f0;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.dark .spinner {
  border-color: #1e293b;
  border-top-color: #3b82f6;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-leave-to {
  opacity: 0;
}
</style>