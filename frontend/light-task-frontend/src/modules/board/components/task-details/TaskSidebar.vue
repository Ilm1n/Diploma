<script setup lang="ts">
import { useBoardStore } from '../../store/board.store';
import { TaskPriority } from '@/api/client';

// UI
import Select from 'primevue/select';
import MultiSelect from 'primevue/multiselect';
import UserAvatar from '@/shared/ui/UserAvatar.vue';

const store = useBoardStore();

const assigneeId = defineModel<number | null>('assigneeId');
const priority = defineModel<TaskPriority | null>('priority');
const tagIds = defineModel<number[]>('tagIds', { default: [] });

const priorityOptions = [
  { label: 'Критический', value: TaskPriority.CRITICAL },
  { label: 'Высокий', value: TaskPriority.HIGH },
  { label: 'Средний', value: TaskPriority.MEDIUM },
  { label: 'Низкий', value: TaskPriority.LOW }
];
</script>

<template>
  <div class="flex flex-col gap-6">
    <slot name="meta"></slot>

    <h4 class="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500">
      Свойства
    </h4>

    <!-- Исполнитель -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 ml-1">Исполнитель</label>
      <Select
          v-model="assigneeId"
          :options="store.members"
          filter
          showClear
          optionLabel="user.username"
          optionValue="user.id"
          placeholder="Не назначен"
          class="w-full"
          fluid
      >
        <template #value="slotProps">
          <div v-if="slotProps.value" class="flex items-center gap-2">
            <UserAvatar
                :image="store.members.find(m => m.user.id === slotProps.value)?.user.avatarUrl || undefined"
                :label="store.members.find(m => m.user.id === slotProps.value)?.user.avatarUrl ? undefined : store.members.find(m => m.user.id === slotProps.value)?.user.username[0]"
                size="sm"
            />
            <span class="text-sm">{{ store.members.find(m => m.user.id === slotProps.value)?.user.username }}</span>
          </div>
          <span v-else class="text-sm text-slate-400">{{ slotProps.placeholder }}</span>
        </template>
        <template #option="slotProps">
          <div class="flex items-center gap-2">
            <UserAvatar
                :image="slotProps.option.user.avatarUrl"
                :label="slotProps.option.user.avatarUrl? undefined : slotProps.option.user.username[0]"
                size="sm" />
            <span class="text-sm">{{ slotProps.option.user.username }}</span>
          </div>
        </template>
      </Select>
    </div>

    <!-- Приоритет -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 ml-1">Приоритет</label>
      <Select
          v-model="priority"
          :options="priorityOptions"

          optionLabel="label"
          optionValue="value"
          placeholder="Без приоритета"
          class="w-full"
          fluid
      />
    </div>

    <!-- Теги -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 ml-1">Теги</label>
      <MultiSelect
          v-model="tagIds"
          :options="store.tags"
          optionLabel="name"
          optionValue="id"
          placeholder="Добавить теги"
          class="w-full"
          display="chip"
          filter
          fluid
      >

        <template #value="slotProps">
          <div v-if="slotProps.value && slotProps.value.length > 0" class="flex flex-wrap gap-1">
            <span
                v-for="tagId in slotProps.value"
                :key="tagId"
                class="text-[10px] font-bold px-2 py-0.5 rounded text-white shadow-sm"
                :style="{ backgroundColor: store.tags.find(t => t.id === tagId)?.color || '#9CA3AF' }"
            >
              {{ store.tags.find(t => t.id === tagId)?.name }}
            </span>
          </div>
          <span v-else class="text-sm text-slate-400">{{ slotProps.placeholder }}</span>
        </template>

        <!-- Слот для элементов в выпадающем списке -->
        <template #option="slotProps">
          <div class="flex items-center gap-2">
            <span
                class="w-3 h-3 rounded-full shadow-sm"
                :style="{ backgroundColor: slotProps.option.color }"
            ></span>
            <span class="text-sm">{{ slotProps.option.name }}</span>
          </div>
        </template>
      </MultiSelect>
    </div>
  </div>
</template>