<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useBoardStore } from '@/modules/board/store/board.store';
import { useAuthStore } from '@/modules/auth/store/auth.store';
import { useToast } from 'primevue/usetoast';
import { useTheme } from "@/composables/useTheme";
import { getErrorMessage } from "@/utils/error";

// UI
import ProgressSpinner from 'primevue/progressspinner';
import Button from 'primevue/button';

const route = useRoute();
const router = useRouter();
const boardStore = useBoardStore();
const authStore = useAuthStore();
const toast = useToast();
const { isDark, toggleTheme } = useTheme();

const token = route.params.token as string;
const error = ref<string | null>(null);
const isLoading = ref(true);

const goBack = () => {
  if (window.history.length > 1) {
    router.back();
  } else {
    router.push('/');
  }
};

const processInvitation = async () => {
  if (!authStore.isAuthenticated) {
    // Сохраняем токен и отправляем на регистрацию
    sessionStorage.setItem('pendingInviteToken', token);
    await router.push({ name: 'register', query: { invite: 'true' } });
    return;
  }

  try {
    const res = await boardStore.acceptInvitation(token);
    toast.add({
      severity: 'success',
      summary: 'Успех!',
      detail: res.message || 'Вы присоединились к проекту',
      life: 3000
    });

    await router.push(`/projects/${res.projectId}/board`);
  } catch (e: any) {
    // Используем наш хелпер для извлечения ошибки
    error.value = getErrorMessage(e);
    isLoading.value = false;
  }
};

onMounted(() => {
  processInvitation();
});
</script>

<template>
  <div class="min-h-screen flex overflow-hidden relative items-center justify-center bg-gray-50 dark:bg-dark-bg p-6 transition-colors duration-300">
    <div class="absolute top-[-5%] left-[-5%] w-48 h-48 sm:w-64 sm:h-64 md:w-80 md:h-80 lg:w-96 lg:h-96 bg-primary-500/20 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-[-5%] right-[-5%] w-48 h-48 sm:w-64 sm:h-64 md:w-80 md:h-80 lg:w-96 lg:h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"></div>

    <!-- Theme Toggle -->
    <button
        @click="toggleTheme"
        class="absolute top-6 right-6 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-dark-surface transition-colors z-20"
    >
      <i :class="isDark ? 'pi pi-sun text-yellow-400' : 'pi pi-moon text-slate-600'" style="font-size: 1.5rem"></i>
    </button>

    <div class="max-w-md w-full text-center">


      <!-- СОСТОЯНИЕ ЗАГРУЗКИ -->
      <div v-if="isLoading && !error" class="space-y-6 animate-fade-in">
        <div class="flex justify-center">
          <ProgressSpinner style="width: 50px; height: 50px" strokeWidth="4" fill="transparent" animationDuration=".5s" />
        </div>
        <div>
          <h1 class="text-2xl font-black text-slate-800 dark:text-white mb-2 tracking-tight uppercase">
            Kantano
          </h1>
          <p class="text-slate-500 dark:text-slate-400 font-medium">
            Проверяем приглашение и готовим рабочее пространство...
          </p>
        </div>
      </div>

      <!-- СОСТОЯНИЕ ОШИБКИ -->
      <div v-if="error" class="relative bg-white dark:bg-dark-surface p-8 rounded-[2.5rem] shadow-xl border border-gray-100 dark:border-dark-border animate-scale-in">
        <div class="w-16 h-16 bg-red-50 dark:bg-red-900/10 text-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <i class="pi pi-exclamation-circle text-3xl"></i>
        </div>

        <h1 class="text-xl font-bold text-slate-800 dark:text-white mb-4">
          Не удалось войти в проект
        </h1>

        <p class="text-slate-500 dark:text-slate-400 mb-8 leading-relaxed text-sm">
          {{ error }}
        </p>

        <div class="flex flex-col gap-3">
          <Button
              label="Вернуться назад"
              outlined
              class="w-full !rounded-xl !border-slate-200 dark:!border-slate-700 !text-slate-600 dark:!text-slate-300"
              @click="goBack"
          />
          <Button
              label="На главную"
              class="w-full !bg-primary-600 !border-none !rounded-xl !text-white !font-bold"
              @click="router.push('/')"
          />
        </div>
      </div>

      <!-- Footer Branding -->
      <p class="mt-12 text-[10px] text-slate-400 uppercase tracking-[0.2em] font-black opacity-50">
        Kantano
      </p>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

.animate-scale-in {
  animation: scaleIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>