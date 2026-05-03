<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { useHead } from '@unhead/vue';
import ProgressSpinner from 'primevue/progressspinner';
import { useAuthStore } from '@/modules/auth/store/auth.store';
import { getSafeInternalPath } from '@/modules/auth/lib/yandex-auth';

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const toast = useToast();
const message = ref('Завершаем вход через Yandex...');

onMounted(async () => {
  const restored = await authStore.restoreSession();

  if (!restored) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка входа',
      detail: 'Не удалось завершить вход через Yandex. Попробуйте ещё раз.',
      life: 5000,
    });
    await router.replace('/login');
    return;
  }

  const nextPath = getSafeInternalPath(route.query.next);
  sessionStorage.removeItem('pendingInviteToken');
  message.value = 'Готово';
  await router.replace(nextPath);
});

useHead({
  title: 'Вход через Yandex',
  meta: [{ name: 'robots', content: 'noindex, nofollow' }],
});
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-slate-50 dark:bg-dark-bg">
    <div class="flex flex-col items-center gap-4 text-center">
      <ProgressSpinner
          class="w-12 h-12"
          strokeWidth="5"
      />
      <p class="text-base font-medium text-slate-700 dark:text-slate-200">
        {{ message }}
      </p>
    </div>
  </div>
</template>
