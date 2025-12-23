<script
    setup
    lang="ts"
>
import type {ProjectRead} from '@/api/client';
import {computed} from 'vue';

const props = defineProps<{
  project: ProjectRead;
}>();

// Форматируем дату (можно вынести в utils)
const formattedDate = computed(() => {
  return new Date(props.project.updatedAt).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short'
  });
});

// Определяем роль для бейджика
const roleLabel = computed(() => {
  if (props.project.currentUserRole === 'OWNER') return 'Владелец';
  if (props.project.currentUserRole === 'MANAGER') return 'Менеджер';
  return 'Участник';
});
</script>

<template>
  <router-link
      :to="`/projects/${project.id}`"
      class="group relative flex flex-col justify-between h-32 p-5 bg-white dark:bg-dark-surface rounded-xl border border-gray-300 dark:border-dark-border hover:shadow-lg hover:-translate-y-1 transition-all duration-300 overflow-hidden"
  >
    <!-- Цветная полоса слева -->
    <div
        class="absolute left-0 top-0 bottom-0 w-2 transition-all duration-300 group-hover:w-2"
        :style="{ backgroundColor: project.color || '#3B82F6' }"
    ></div>

    <!-- Контент -->
    <div class="pl-2">
      <h3 class="font-bold text-lg text-slate-800 dark:text-white truncate mb-1">
        {{ project.name }}
      </h3>
      <p class="text-sm text-slate-500 dark:text-slate-400 line-clamp-2">
        {{ project.description || 'Нет описания' }}
      </p>
    </div>

    <!-- Футер карточки -->
    <div class="pl-2 flex justify-between items-center mt-auto">
      <span class="text-xs text-slate-400 font-medium">Обновлено {{ formattedDate }}</span>

      <!-- Бейдж роли -->
      <span
          class="text-[10px] uppercase font-bold px-2 py-1 rounded-md bg-gray-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
      >
        {{ roleLabel }}
      </span>
    </div>
  </router-link>
</template>