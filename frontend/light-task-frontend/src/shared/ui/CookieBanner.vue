<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';
import Button from 'primevue/button';
import Dialog from 'primevue/dialog';

import {
  getStoredConsent,
  onOpenCookieSettingsRequested,
  setConsent,
  type CookieConsent,
} from '@/shared/consent/consent';

const isBannerVisible = ref(false);
const isSettingsVisible = ref(false);
const analyticsEnabled = ref(false);

let removeOpenSettingsListener: (() => void) | null = null;

onMounted(() => {
  const saved = getStoredConsent();
  analyticsEnabled.value = saved?.analytics ?? false;

  if (!saved) {
    setTimeout(() => {
      isBannerVisible.value = true;
    }, 800);
  }

  removeOpenSettingsListener = onOpenCookieSettingsRequested(() => {
    isSettingsVisible.value = true;
  });
});

onBeforeUnmount(() => {
  removeOpenSettingsListener?.();
});

function applyConsent(analytics: boolean): CookieConsent {
  const consent = setConsent(analytics);
  analyticsEnabled.value = consent.analytics;
  isBannerVisible.value = false;
  isSettingsVisible.value = false;
  return consent;
}

function acceptAll(): void {
  applyConsent(true);
}

function acceptNecessaryOnly(): void {
  applyConsent(false);
}

function saveSettings(): void {
  applyConsent(analyticsEnabled.value);
}

function openSettings(): void {
  isSettingsVisible.value = true;
}
</script>

<template>
  <Transition name="slide-up">
    <div
      v-if="isBannerVisible"
      role="dialog"
      aria-label="Настройки cookie"
      class="fixed bottom-6 left-6 right-6 md:left-auto md:right-8 md:max-w-lg z-[2000]"
    >
      <div class="bg-white dark:bg-dark-surface border border-slate-200 dark:border-dark-border shadow-2xl rounded-2xl p-6">
        <div class="flex items-start gap-4">
          <div class="p-3 rounded-xl bg-primary-50 dark:bg-primary-500/10 text-primary-600 shrink-0">
            <i class="pi pi-shield text-xl"></i>
          </div>

          <div class="flex flex-col gap-4">
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white mb-1">Настройки cookie</h3>
              <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                Мы используем обязательные cookie для работы сайта и аналитические cookie для улучшения продукта.
                Вы можете принять все или оставить только обязательные.
              </p>
            </div>

            <div class="flex flex-wrap items-center gap-2">
              <Button
                label="Принять все"
                class="!bg-primary-600 !border-none !text-white !px-5 !py-2 !text-sm !font-bold"
                @click="acceptAll"
              />
              <Button
                label="Только обязательные"
                severity="secondary"
                outlined
                class="!px-4 !py-2 !text-sm"
                @click="acceptNecessaryOnly"
              />
              <Button
                label="Настроить"
                text
                size="small"
                class="!text-primary-700 dark:!text-primary-300 !font-semibold"
                @click="openSettings"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <Dialog
    v-model:visible="isSettingsVisible"
    modal
    header="Настройки cookie"
    :style="{ width: '560px', maxWidth: '95vw' }"
    :draggable="false"
  >
    <div class="flex flex-col gap-5 py-1">
      <p class="text-sm text-slate-500 dark:text-slate-400">
        Выберите, какие cookie разрешены. Обязательные cookie нужны для авторизации и безопасности, их нельзя отключить. В будущем вы сможете найти настройки cookie в профиле или в нижней части главной страницы.
      </p>

      <div class="rounded-xl border border-slate-200 dark:border-slate-700 p-4 flex items-start justify-between gap-4">
        <div>
          <h4 class="font-semibold text-slate-800 dark:text-white">Обязательные cookie</h4>
          <p class="text-sm text-slate-500 dark:text-slate-400">Нужны для базовой работы приложения.</p>
        </div>
        <span class="text-xs font-semibold px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">Всегда включены</span>
      </div>

      <div class="rounded-xl border border-slate-200 dark:border-slate-700 p-4 flex items-start justify-between gap-4">
        <div>
          <h4 class="font-semibold text-slate-800 dark:text-white">Аналитические cookie</h4>
          <p class="text-sm text-slate-500 dark:text-slate-400">Помогают нам понимать поведение пользователей и улучшать продукт.</p>
        </div>

        <label class="inline-flex items-center cursor-pointer select-none">
          <input v-model="analyticsEnabled" type="checkbox" class="sr-only peer" />
          <span
            class="relative w-11 h-6 rounded-full transition-colors duration-200"
            :class="analyticsEnabled ? 'bg-primary-600' : 'bg-slate-200 dark:bg-slate-700'"
          >
            <span
              class="absolute top-[2px] left-[2px] h-5 w-5 rounded-full bg-white border border-slate-300 transition-transform duration-200"
              :style="{ transform: analyticsEnabled ? 'translateX(20px)' : 'translateX(0)' }"
            />
          </span>
        </label>
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <Button label="Только обязательные" text @click="acceptNecessaryOnly" />
        <Button label="Сохранить" class="!bg-primary-600 !border-none !text-white" @click="saveSettings" />
      </div>
    </div>
  </Dialog>

</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
