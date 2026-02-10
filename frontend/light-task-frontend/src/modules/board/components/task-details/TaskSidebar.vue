<script setup lang="ts">
import {computed} from 'vue';
import {useBoardStore} from '../../store/board.store';
import {TaskPriority} from '@/api/client';

import Dropdown from 'primevue/dropdown';
import MultiSelect from 'primevue/multiselect';
import UserAvatar from '@/shared/ui/UserAvatar.vue';

const store = useBoardStore();

const selectedAssignee = computed({
  get: () => store.selectedTask?.assigneeId || null,
  set: (assigneeId) => {
    if (store.selectedTask) {
      store.updateTask(store.selectedTask.id, { assigneeId });
    }
  }
});

const selectedPriority = computed({
  get: () => store.selectedTask?.priority || null,
  set: (priority) => {
    if (store.selectedTask && priority) {
      store.updateTask(store.selectedTask.id, { priority });
    }
  }
});

const selectedTags = computed({
  get: () => store.selectedTask?.tags?.map(t => t.id) || [],
  set: (tagIds) => {
    if (store.selectedTask) {
      store.updateTask(store.selectedTask.id, { tagIds });
    }
  }
});

const priorityOptions: { label: string, value: TaskPriority }[] = [
  { label: 'Критический', value: TaskPriority.CRITICAL },
  { label: 'Высокий', value: TaskPriority.HIGH },
  { label: 'Средний', value: TaskPriority.MEDIUM },
  { label: 'Низкий', value: TaskPriority.LOW }
];
</script>

<template>
  <div class="flex flex-col gap-6">
    <h4 class="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500">Информация</h4>

    <!-- Assignee -->
    <div class="flex flex-col gap-1.5">
      <span class="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Исполнитель</span>
      <Dropdown v-model="selectedAssignee" showClear :options="store.members" filter optionLabel="user.username" optionValue="user.id" placeholder="Не назначен" class="w-full !text-sm">
        <template #value="slotProps">
          <div v-if="slotProps.value" class="flex items-center gap-2">
            <UserAvatar :image="store.members.find(m => m.user.id === slotProps.value)?.user.avatarUrl || ''" size="sm" />
            <span>{{ store.members.find(m => m.user.id === slotProps.value)?.user.username }}</span>
          </div>
          <span v-else>{{ slotProps.placeholder }}</span>
        </template>
        <template #option="slotProps">
          <div class="flex items-center gap-2">
            <UserAvatar :image="slotProps.option.user.avatarUrl" size="sm" />
            <span>{{ slotProps.option.user.username }}</span>
          </div>
        </template>
      </Dropdown>
    </div>

    <!-- Priority -->
    <div class="flex flex-col gap-1.5">
      <span class="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Приоритет</span>
      <Dropdown v-model="selectedPriority"  :options="priorityOptions" optionLabel="label" optionValue="value" placeholder="Выберите приоритет" class="w-full !text-sm" />
    </div>

    <!-- Tags -->
    <div class="flex flex-col gap-1.5">
      <span class="text-[11px] text-slate-500 dark:text-slate-400 font-medium">Теги</span>
      <MultiSelect v-model="selectedTags" :options="store.tags" optionLabel="name" optionValue="id" placeholder="Добавить теги" class="w-full !text-sm">
        <template #value="slotProps">
          <div class="flex flex-wrap gap-1">
            <span v-for="tagId in slotProps.value" :key="tagId"
                  class="text-[10px] font-bold px-1.5 py-0.5 rounded text-white"
                  :style="{ backgroundColor: store.tags.find(t => t.id === tagId)?.color || '#9CA3AF' }"
            >
              {{ store.tags.find(t => t.id === tagId)?.name }}
            </span>
            <span v-if="!slotProps.value || slotProps.value.length === 0">{{ slotProps.placeholder }}</span>
          </div>
        </template>
        <template #option="slotProps">
          <div class="flex items-center">
            <span class="w-3 h-3 rounded mr-2" :style="{ backgroundColor: slotProps.option.color }"></span>
            <div>{{ slotProps.option.name }}</div>
          </div>
        </template>
      </MultiSelect>
    </div>
  </div>
</template>