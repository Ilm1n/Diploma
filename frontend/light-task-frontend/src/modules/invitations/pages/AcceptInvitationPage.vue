<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useBoardStore } from '@/modules/board/store/board.store';
import { useAuthStore } from '@/modules/auth/store/auth.store';
import { useToast } from 'primevue/usetoast';

// UI
import ProgressSpinner from 'primevue/progressspinner';
import Button from 'primevue/button';

const route = useRoute();
const router = useRouter();
const boardStore = useBoardStore();
const authStore = useAuthStore();
const toast = useToast();

const token = route.params.token as string;
const error = ref<string | null>(null);
const isLoading = ref(true);

const processInvitation = async () => {
  if (!authStore.isAuthenticated) {
    sessionStorage.setItem('pendingInviteToken', token);
    await router.push({name: 'register', query: {invite: 'true'}});
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
    error.value = e.response?.data?.detail || 'Не удалось принять приглашение. Возможно, ссылка истекла.';
    isLoading.value = false;
  }
};

onMounted(() => {
  processInvitation();
});
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg p-6">
    <div class="max-w-md w-full text-center">

      <!-- Состояние загрузки -->
      <div v-if="isLoading && !error" class="flex flex-col items-center gap-6 animate-fade-in">
        <ProgressSpinner style="width: 64px; height: 64px" strokeWidth="4" />
        <div>
          <h1 class="text-2xl font-bold mb-2">Принимаем приглашение...</h1>
          <p class="text-slate-500">Пожалуйста, подождите, мы добавляем вас в проект.</p>
        </div>
      </div>

      <!-- Состояние ошибки -->
      <div v-if="error" class="bg-white dark:bg-dark-surface p-8 rounded-[2rem] shadow-xl border border-red-100 dark:border-red-900/20 animate-scale-in">
        <div class="w-16 h-16 bg-red-50 dark:bg-red-900/20 text-red-500 rounded-full flex items-center justify-center mx-auto mb-6">
          <i class="pi pi-times text-2xl"></i>
        </div>
        <h1 class="text-xl font-bold mb-4">Ой! Что-то пошло не так</h1>
        <p class="text-slate-500 mb-8">{{ error }}</p>
        <Button label="Вернуться на главную" class="w-full !bg-primary-600 !border-none" @click="router.push('/')" />
      </div>

    </div>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.5s ease-out; }
.animate-scale-in { animation: scaleIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes scaleIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
</style>