<script setup lang="ts">
import { ref } from 'vue';
import { useBoardStore } from '../store/board.store';
import { TaskPriority } from '@/api/client';

// UI
import Button from 'primevue/button';
import Popover from 'primevue/popover';
import InputText from 'primevue/inputtext';
import MultiSelect from 'primevue/multiselect';
import IconField from 'primevue/iconfield';
import InputIcon from 'primevue/inputicon';
import UserAvatar from '@/shared/ui/UserAvatar.vue';

const store = useBoardStore();
const op = ref();

const toggle = (event: Event) => {
  op.value.toggle(event);
};

const priorityOptions = [
  { label: 'Критический', value: TaskPriority.CRITICAL },
  { label: 'Высокий', value: TaskPriority.HIGH },
  { label: 'Средний', value: TaskPriority.MEDIUM },
  { label: 'Низкий', value: TaskPriority.LOW }
];
</script>

<template>
  <div class="flex items-center">
    <!-- Кнопка фильтров -->
    <Button
        type="button"
        @click="toggle"
        severity="secondary"
        outlined
        :class="[
        '!px-3 !py-2 !rounded-xl !text-sm transition-all',
        store.isFilterActive
          ? '!bg-primary-600 !border-primary-600 !text-white'
          : '!border-slate-200 dark:!border-dark-border !text-slate-600 dark:!text-slate-400'
      ]"
    >
      <div class="flex items-center gap-2">
        <i class="pi pi-filter" :class="store.isFilterActive ? 'text-white' : 'text-primary-500'"></i>
        <div v-if="store.isFilterActive" class="flex items-center justify-center bg-white text-primary-600 text-[10px] w-4 h-4 rounded-full ml-1">!</div>
      </div>
    </Button>

    <Popover ref="op" class="!w-[calc(100vw-2rem)] ml-5 sm:!ml-0 sm:!w-[380px]">
      <div class="flex flex-col gap-6 p-1">

        <!-- Заголовок  -->
        <div class="flex items-center justify-between border-b border-gray-100 dark:border-dark-border pb-3">
          <div class="flex items-center gap-2">
            <i class="pi pi-sliders-h text-primary-500"></i>
            <span class="font-bold text-slate-800 dark:text-white">Параметры фильтрации</span>
          </div>
          <Button v-if="store.isFilterActive" label="Сбросить" text severity="danger" size="small" class="!py-1 !px-2 !text-[11px] !font-bold" @click="store.resetFilters" />
        </div>

        <!-- Поиск  -->
        <div class="flex flex-col gap-2">
          <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400 ml-1">Поиск по тексту</label>
          <IconField>
            <InputIcon class="pi pi-search" />
            <InputText v-model="store.filters.search" placeholder="Название или описание..." class="w-full !text-sm !py-2.5" fluid />
          </IconField>
        </div>

        <!-- Исполнители  -->
        <div class="flex flex-col gap-2">
          <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400 ml-1">Исполнители</label>
          <MultiSelect
              v-model="store.filters.assigneeIds"
              :options="store.members"
              optionLabel="user.username"
              optionValue="user.id"
              placeholder="Все участники"
              filter
              class="w-full !text-sm"
              fluid
          >
            <template #value="slotProps">
              <div v-if="slotProps.value && slotProps.value.length > 0" class="flex flex-wrap gap-1">
                <div v-for="id in slotProps.value" :key="id" class="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-700 px-2 py-1 rounded-lg">
                  <UserAvatar
                      :image="store.members.find(m => m.user.id === id)?.user.avatarUrl || undefined"
                      :label="store.members.find(m => m.user.id === id)?.user.avatarUrl ? undefined : store.members.find(m => m.user.id === id)?.user.username[0]"
                      size="sm"
                      class="!w-4 !h-4 !text-[8px]"
                  />
                  <span class="text-[11px] font-medium">{{ store.members.find(m => m.user.id === id)?.user.username }}</span>
                </div>
              </div>
              <span v-else class="text-slate-400">{{ slotProps.placeholder }}</span>
            </template>

            <template #option="slotProps">
              <div class="flex items-center gap-2">
                <UserAvatar
                    :image="slotProps.option.user.avatarUrl"
                    :label="slotProps.option.user.avatarUrl ? undefined : slotProps.option.user.username[0]"
                    size="sm"
                />
                <span class="text-sm">{{ slotProps.option.user.username }}</span>
              </div>
            </template>
          </MultiSelect>
        </div>

        <!-- Теги  -->
        <div class="flex flex-col gap-2">
          <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400 ml-1">Теги</label>
          <MultiSelect v-model="store.filters.tagIds" :options="store.tags" optionLabel="name" optionValue="id" placeholder="Любые теги" filter class="w-full !text-sm" fluid>
            <template #value="slotProps">
              <div v-if="slotProps.value && slotProps.value.length > 0" class="flex flex-wrap gap-1">
                <span v-for="tagId in slotProps.value" :key="tagId" class="text-[10px] font-bold px-2 py-0.5 rounded text-white shadow-sm" :style="{ backgroundColor: store.tags.find(t => t.id === tagId)?.color || '#9CA3AF' }">
                  {{ store.tags.find(t => t.id === tagId)?.name }}
                </span>
              </div>
              <span v-else class="text-slate-400">{{ slotProps.placeholder }}</span>
            </template>
            <template #option="slotProps">
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full shadow-sm" :style="{ backgroundColor: slotProps.option.color }"></span>
                <span class="text-sm">{{ slotProps.option.name }}</span>
              </div>
            </template>
          </MultiSelect>
        </div>

        <!-- Приоритет  -->
        <div class="flex flex-col gap-2">
          <label class="text-[10px] font-bold uppercase tracking-widest text-slate-400 ml-1">Срочность</label>
          <MultiSelect v-model="store.filters.priorities" :options="priorityOptions" optionLabel="label" optionValue="value" placeholder="Любой приоритет" class="w-full !text-sm" fluid />
        </div>

      </div>
    </Popover>
  </div>
</template>