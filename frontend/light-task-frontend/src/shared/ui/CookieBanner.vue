<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useStorage } from '@vueuse/core';
import Button from 'primevue/button';

const cookieConsent = useStorage('kantano-cookie-consent', false);
const isVisible = ref(false);

onMounted(() => {
  if (!cookieConsent.value) {
    setTimeout(() => {
      isVisible.value = true;
    }, 1000);
  }
});

const acceptCookies = () => {
  cookieConsent.value = true;
  isVisible.value = false;
};
</script>

<template>
  <Transition name="slide-up">
    <div
        v-if="isVisible"
        role="alert"
        class="fixed bottom-6 left-6 right-6 md:left-auto md:right-8 md:max-w-md z-[2000]"
    >
      <div class="bg-white dark:bg-dark-surface border border-slate-200 dark:border-dark-border shadow-2xl rounded-2xl p-6">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-xl bg-primary-50 dark:bg-primary-500/10 text-primary-600 shrink-0">
            <i class="pi pi-info-circle text-xl"></i>
          </div>

          <div class="flex flex-col gap-4">
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white mb-1">Мы используем куки</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                Kantano использует файлы cookie для улучшения работы сервиса и обеспечения безопасности.
                Оставаясь на сайте, вы соглашаетесь с нашей
                <a href="#" class="text-primary-600 hover:underline font-medium">политикой конфиденциальности</a>.
              </p>
            </div>

            <div class="flex items-center gap-3">
              <Button
                  label="Принять"
                  class="!bg-primary-600 !border-none !text-white !px-6 !py-2 !text-sm !font-bold"
                  @click="acceptCookies"
              />
              <button
                  @click="isVisible = false"
                  class="text-xs  text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors px-2"
              >
                Позже
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>