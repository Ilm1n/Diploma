<script setup lang="ts">
// ... (Весь скрипт оставляем БЕЗ ИЗМЕНЕНИЙ, он правильный) ...
import { ref, computed } from 'vue';
import type { ColumnRead } from '@/api/client';
import { useBoardStore } from '../store/board.store';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';
import { getPlural } from '@/utils/plural';

import Button from 'primevue/button';
import Menu from 'primevue/menu';
import InputText from 'primevue/inputtext';

const props = defineProps<{
  column: ColumnRead;
}>();

const store = useBoardStore();
const confirm = useConfirm();
const toast = useToast();

const isRenaming = ref(false);
const newName = ref(props.column.name);
const nameInput = ref();

const startRename = () => {
  newName.value = props.column.name;
  isRenaming.value = true;
  setTimeout(() => nameInput.value?.$el?.focus(), 0);
};

const saveRename = async () => {
  if (!newName.value.trim() || newName.value === props.column.name) {
    isRenaming.value = false;
    return;
  }

  try {
    await store.updateColumn(props.column.id, { name: newName.value });
    isRenaming.value = false;
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось переименовать', life: 3000 });
  }
};

const cancelRename = () => {
  isRenaming.value = false;
  newName.value = props.column.name;
};

const tasksCountLabel = computed(() => {
  const count = props.column.tasks?.length || 0;
  const word = getPlural(count, ['задача', 'задачи', 'задач']);
  return `${count} ${word}`;
});

const menu = ref();
const onMenuClick = (event: Event) => {
  menu.value.toggle(event);
};

const items = [
  {
    label: 'Переименовать',
    icon: 'pi pi-pencil',
    command: startRename
  },
  {
    separator: true
  },
  {
    label: 'Удалить',
    icon: 'pi pi-trash',
    class: 'text-red-500',
    command: () => {
      menu.value?.hide?.();
      confirm.require({
        message: 'Вы уверены, что хотите удалить эту колонку?',
        header: 'Подтверждение',
        icon: 'pi pi-info-circle',
        rejectLabel: 'Отмена',
        acceptLabel: 'Удалить',
        rejectClass: 'p-button-secondary p-button-outlined',
        acceptClass: 'p-button-danger',
        accept: async () => {
          await store.deleteColumn(props.column.id);
          toast.add({ severity: 'success', summary: 'Удалено', detail: 'Колонка удалена', life: 3000 });
        }
      });
    }
  }
];
</script>

<template>
  <!--
    FIX: Внешняя обертка теперь h-full (на всю высоту экрана).
    Это решает проблему с Drag&Drop в нижней части экрана.
    Сама обертка прозрачная, стили перенесли внутрь.
  -->
  <div class="w-80 h-full shrink-0 flex flex-col">

    <!-- Визуальная карточка колонки -->
    <div class="w-full max-h-full flex flex-col bg-gray-50 dark:bg-dark-surface rounded-xl border border-gray-200 dark:border-dark-border shadow-sm transition-colors duration-300">

      <!-- HEADER (Drag Handle) -->
      <div
          class="column-drag-handle p-3 border-b border-gray-200 dark:border-dark-border/50 flex justify-between items-start gap-2 cursor-grab active:cursor-grabbing group"
      >
        <!-- Title Mode -->
        <div v-if="!isRenaming" class="flex-1 min-w-0" @dblclick="startRename">
          <h3 class="font-bold text-slate-700 dark:text-slate-200 truncate leading-6">
            {{ column.name }}
          </h3>
          <span class="text-xs text-slate-400 font-medium">
            {{ tasksCountLabel }}
          </span>
        </div>

        <!-- Edit Mode -->
        <div v-else class="flex-1">
          <InputText
              ref="nameInput"
              v-model="newName"
              class="w-full !py-1 !px-2 !text-sm"
              @keydown.enter="saveRename"
              @keydown.esc="cancelRename"
              @blur="saveRename"
              @mousedown.stop
          />
        </div>

        <!-- Actions Menu -->
        <Button
            icon="pi pi-ellipsis-h"
            text
            rounded
            size="small"
            class="!w-8 !h-8 !text-slate-400 hover:!bg-gray-100 dark:hover:!bg-slate-700/50 hover:!text-slate-600 dark:hover:!text-slate-200  transition-opacity"
            @click="onMenuClick"
            aria-haspopup="true"
            aria-controls="column_menu"
        />
        <Menu ref="menu" id="column_menu" :model="items" :popup="true" />
      </div>

      <!-- TASKS AREA -->
      <div class="flex-1 p-2 overflow-y-auto min-h-[100px] custom-scrollbar space-y-2">
        <div
            v-for="task in (column.tasks || [])"
            :key="task.id"
            class="p-3 bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 shadow-sm"
        >
          <span class="text-slate-800 dark:text-slate-200 text-sm font-medium">{{ task.title }}</span>
        </div>
      </div>

      <!-- FOOTER -->
      <div class="p-2 pt-0">
        <button
            class="w-full py-2 flex items-center justify-start px-2 gap-2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-gray-200/50 dark:hover:bg-slate-700/50 rounded-lg transition-colors text-sm font-medium"
        >
          <i class="pi pi-plus"></i>
          Добавить задачу
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background: #475569;
}
</style>