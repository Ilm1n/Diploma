<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useBoardStore } from '../../store/board.store';
import { watchDebounced } from '@vueuse/core';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';

// UI Components
import Drawer from 'primevue/drawer';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Skeleton from 'primevue/skeleton';
import Button from 'primevue/button';

const route = useRoute();
const router = useRouter();
const store = useBoardStore();
const toast = useToast();
const confirm = useConfirm();

const isVisible = ref(false);
const localTitle = ref('');
const localDescription = ref('');

// Sync with URL
watch(() => route.query.taskId, async (newId) => {
  if (newId) {
    const id = Number(newId);
    if (!isNaN(id)) {
      isVisible.value = true;
      await store.fetchTaskDetails(id);
      if (store.selectedTask) {
        localTitle.value = store.selectedTask.title;
        localDescription.value = store.selectedTask.description || '';
      }
    }
  } else {
    isVisible.value = false;
  }
}, { immediate: true });

const onClose = () => {
  isVisible.value = false;
  const query = { ...route.query };
  delete query.taskId;
  router.push({ query });
};

// Auto-save Title
const saveTitle = async () => {
  if (!store.selectedTask) return;
  if (localTitle.value.trim() === store.selectedTask.title) return;
  try {
    await store.updateTask(store.selectedTask.id, { title: localTitle.value });
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось сохранить заголовок', life: 3000 });
    localTitle.value = store.selectedTask.title;
  }
};

watchDebounced(
    localDescription,
    async (newVal) => {
      if (!store.selectedTask) return;
      if (newVal === (store.selectedTask.description || '')) return;
      try {
        await store.updateTask(store.selectedTask.id, { description: newVal });
      } catch (e) {
        console.error(e);
      }
    },
    { debounce: 1000 }
);

const deleteTask = () => {
  const taskId = store.selectedTask?.id;
  if (!taskId) return;

  confirm.require({
    message: 'Вы уверены, что хотите удалить эту задачу? Это действие необратимо.',
    header: 'Удаление задачи',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Отмена',
    acceptLabel: 'Удалить',
    rejectClass: 'p-button-secondary p-button-outlined',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await store.deleteTask(taskId);
        toast.add({ severity: 'success', summary: 'Удалено', detail: 'Задача удалена', life: 3000 });
        onClose();
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось удалить задачу', life: 3000 });
      }
    }
  });
};
</script>

<template>
  <Drawer
      v-model:visible="isVisible"
      position="right"
      class="!w-full md:!w-[600px] !bg-white dark:!bg-dark-surface !border-l dark:!border-dark-border !transition-colors !duration-100"
      :pt="{
      mask: { class: 'backdrop-blur-[1px]' },
      header: { class: '!bg-white dark:!bg-dark-surface !border-b !border-gray-200 dark:!border-dark-border !p-5' },
      content: { class: '!bg-white dark:!bg-dark-surface !p-6' },
      closeButton: { class: 'hover:!bg-gray-100 dark:hover:!bg-slate-800 !text-slate-500' }
      }"
      @hide="onClose"
  >
  <template #header>
    <div class="flex items-center gap-3 ">
      <div class="p-2 rounded-lg bg-primary-50 dark:!bg-dark-surface">
        <i class="pi pi-check-square text-primary-600"></i>
      </div>
      <span class="font-bold text-slate-800 dark:text-white text-base">
          Детали задачи
        </span>
    </div>
  </template>

  <!-- LOADING STATE -->
  <div v-if="store.isTaskLoading || !store.selectedTask" class="space-y-6">
    <Skeleton height="2.5rem" class="!bg-gray-100 dark:!bg-slate-800" />
    <div class="space-y-2">
      <Skeleton width="40%" height="1.2rem" class="!bg-gray-100 dark:!bg-slate-800" />
      <Skeleton height="8rem" class="!bg-gray-100 dark:!bg-slate-800" />
    </div>
  </div>

  <!-- CONTENT -->
  <div v-else class="flex flex-col gap-8">

    <!-- Task Title Section -->
    <div class="group flex flex-col gap-1">
      <label class="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 ml-1">Название</label>
      <InputText
          v-model="localTitle"
          class="!text-xl !font-bold !bg-transparent !border-transparent hover:!bg-gray-50 dark:hover:!bg-slate-800/50 focus:!border-primary-500 !px-2 !transition-all dark:!text-white"
          placeholder="Введите название задачи..."
          @blur="saveTitle"
          @keydown.enter="($event.target as HTMLInputElement).blur()"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Left Column -->
      <div class="lg:col-span-2 flex flex-col gap-6">
        <div class="flex flex-col gap-3">
          <div class="flex items-center gap-2 text-slate-800 dark:text-slate-200 font-bold text-sm">
            <i class="pi pi-align-left text-slate-400"></i>
            Описание
          </div>
          <Textarea
              v-model="localDescription"
              autoResize
              rows="6"
              placeholder="Добавьте описание задачи (Markdown...)"
              class="w-full !bg-gray-50 dark:!bg-dark-bg/40 !border-gray-200 dark:!border-dark-border
                       focus:!bg-white dark:focus:!bg-dark-bg focus:!ring-1 focus:!ring-primary-500
                       !text-slate-700 dark:!text-slate-300
                       !transition-all !rounded-lg !p-3 !text-sm !leading-relaxed"
          />
          <div class="flex justify-between items-center text-[11px] text-slate-400">
            <span>Автосохранение включено</span>
            <span class="flex items-center gap-1"><i class="pi pi-info-circle"></i> Markdown</span>
          </div>
        </div>
      </div>


      <!-- Sidebar Right -->
      <!-- TODO: добавить реальные опции -->
      <div class="lg:col-span-1 flex flex-col gap-6">
        <div>
          <h4 class="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 mb-3">Информация</h4>
          <div class="space-y-3">
            <div class="flex flex-col gap-1.5 p-3 rounded-lg border border-gray-100 dark:border-dark-border bg-gray-50/50 dark:bg-dark-bg/20">
              <span class="text-[11px] text-slate-500 dark:text-slate-400">Статус</span>
              <span class="text-xs font-semibold dark:text-slate-200 flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full bg-primary-500"></span> В работе
                </span>
            </div>
          </div>
        </div>

        <div class="pt-4 border-t border-gray-100 dark:border-dark-border">
          <Button
              label="Удалить задачу"
              icon="pi pi-trash"
              severity="danger"
              text
              class="!w-full !justify-start !text-xs !font-bold !py-2 hover:!bg-red-50 dark:hover:!bg-red-900/10"
              @click="deleteTask"
          />
        </div>
      </div>
    </div>
  </div>
  </Drawer>
</template>

<style scoped>
/* Скроллбар в стиле дашборда */
textarea::-webkit-scrollbar {
  width: 4px;
}
textarea::-webkit-scrollbar-track {
  @apply bg-transparent;
}
textarea::-webkit-scrollbar-thumb {
  @apply bg-gray-200 dark:bg-slate-700 rounded-full;
}

/* Убираем стандартное свечение PrimeVue */
:deep(.p-inputtext:focus) {
  box-shadow: none !important;
}

/* Анимация появления контента */
.flex-col {
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(10px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>