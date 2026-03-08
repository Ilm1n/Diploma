<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useBoardStore } from "../../store/board.store";
import { watchDebounced } from "@vueuse/core";
import { useToast } from "primevue/usetoast";
import { getErrorMessage } from "@/utils/error";
import { useConfirm } from "primevue/useconfirm";
import type { TaskPriority, TaskUpdate } from "@/api/client";

// UI Components
import Drawer from "primevue/drawer";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Skeleton from "primevue/skeleton";
import Button from "primevue/button";
import TaskSidebar from "./TaskSidebar.vue";

const route = useRoute();
const router = useRouter();
const store = useBoardStore();
const toast = useToast();
const confirm = useConfirm();

const isVisible = ref(false);

// --- Локальное состояние (Single Source of Truth для формы) ---
const localTitle = ref("");
const localDescription = ref("");
const localAssigneeId = ref<number | null>(null);
const localPriority = ref<TaskPriority | null>(null);
const localTagIds = ref<number[]>([]);

// Состояния сохранения
const isSaving = ref(false);
const lastSavedAt = ref<Date | null>(null);

// Форматирование времени сохранения
const lastSavedTime = computed(() => {
  if (!lastSavedAt.value) return "";
  return lastSavedAt.value.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
});

// Форматирование дат создания/обновления
const formatDate = (dateStr?: string) => {
  if (!dateStr) return "—";
  return new Date(dateStr).toLocaleString("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// --- Инициализация при открытии ---
watch(
  () => route.query.taskId,
  async (newId) => {
    if (newId) {
      const id = Number(newId);
      if (!isNaN(id)) {
        isVisible.value = true;
        await store.fetchTaskDetails(id);

        // Заполняем локальные поля из стора
        if (store.selectedTask) {
          localTitle.value = store.selectedTask.title;
          localDescription.value = store.selectedTask.description || "";
          localAssigneeId.value = store.selectedTask.assigneeId || null;
          localPriority.value = store.selectedTask.priority || null;
          localTagIds.value = store.selectedTask.tags?.map((t) => t.id) || [];

          lastSavedAt.value = null; // Сброс статуса
        }
      }
    } else {
      isVisible.value = false;
    }
  },
  { immediate: true },
);

const onClose = () => {
  isVisible.value = false;
  const query = { ...route.query };
  delete query.taskId;
  router.push({ query });
};

// --- УНИВЕРСАЛЬНАЯ ФУНКЦИЯ СОХРАНЕНИЯ ---
const performSave = async (payload: TaskUpdate) => {
  if (!store.selectedTask) return;

  isSaving.value = true;
  try {
    await store.updateTask(store.selectedTask.id, payload);
    lastSavedAt.value = new Date();
  } catch (e) {
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: getErrorMessage(e),
      life: 3000,
    });
  } finally {
    isSaving.value = false;
  }
};

// 1. Auto-save Title (Blur)
const saveTitle = () => {
  if (!store.selectedTask) return;
  if (!localTitle.value.trim()) {
    localTitle.value = store.selectedTask.title;
    return;
  }
  if (localTitle.value.trim() === store.selectedTask.title) return;
  performSave({ title: localTitle.value });
};

// 2. Auto-save Description (Debounce)
watchDebounced(
  localDescription,
  async (newVal) => {
    if (!store.selectedTask) return;
    if (newVal === (store.selectedTask.description || "")) return;
    await performSave({ description: newVal });
  },
  { debounce: 1000 },
);

// 3. Auto-save Sidebar Fields (Watchers)
// Важно проверять на равенство, чтобы не триггерить сохранение при инициализации
watch(localAssigneeId, (newVal) => {
  if (store.selectedTask && newVal !== store.selectedTask.assigneeId) {
    performSave({ assigneeId: newVal });
  }
});

watch(localPriority, (newVal) => {
  if (store.selectedTask && newVal !== store.selectedTask.priority) {
    performSave({ priority: newVal });
  }
});

watch(localTagIds, (newVal) => {
  // Сравниваем массивы (грубо, но для ID пойдет)
  const currentIds = store.selectedTask?.tags?.map((t) => t.id) || [];
  const isSame =
    newVal.length === currentIds.length &&
    newVal.every((id) => currentIds.includes(id));

  if (store.selectedTask && !isSame) {
    performSave({ tagIds: newVal });
  }
});

// 4. Ручное сохранение (Кнопка внизу - атомарное)
const saveAllAndClose = async () => {
  if (!localTitle.value.trim()) {
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: "Название задачи не может быть пустым",
      life: 3000,
    });
    return;
  }

  await performSave({
    title: localTitle.value,
    description: localDescription.value,
    assigneeId: localAssigneeId.value,
    priority: localPriority.value,
    tagIds: localTagIds.value,
  });
  onClose();
};

const deleteTask = () => {
  const taskId = store.selectedTask?.id;
  if (!taskId) return;

  confirm.require({
    message:
      "Вы уверены, что хотите удалить эту задачу? Это действие необратимо.",
    header: "Удаление задачи",
    icon: "pi pi-exclamation-triangle",
    rejectLabel: "Отмена",
    acceptLabel: "Удалить",
    rejectClass: "p-button-secondary p-button-outlined",
    acceptClass: "p-button-danger !text-white",
    accept: async () => {
      try {
        await store.deleteTask(taskId);
        toast.add({
          severity: "success",
          summary: "Удалено",
          detail: "Задача удалена",
          life: 3000,
        });
        onClose();
      } catch (e) {
        toast.add({
          severity: "error",
          summary: "Ошибка",
          detail: getErrorMessage(e),
          life: 3000,
        });
      }
    },
  });
};
</script>

<template>
  <Drawer
    v-model:visible="isVisible"
    position="right"
    class="!w-full md:!w-[700px] !bg-white dark:!bg-dark-surface !border-l dark:!border-dark-border !transition-colors !duration-100"
    :pt="{
      mask: { class: 'backdrop-blur-[1px]' },
      header: {
        class:
          '!bg-white dark:!bg-dark-surface !border-b !border-gray-200 dark:!border-dark-border !p-5',
      },
      content: {
        class:
          '!bg-white dark:!bg-dark-surface !p-6 !overflow-hidden flex flex-col',
      },
      closeButton: {
        class: 'hover:!bg-gray-100 dark:hover:!bg-slate-800 !text-slate-500',
      },
    }"
    @hide="onClose"
  >
    <template #header>
      <div class="flex items-center gap-3">
        <div class="p-2 rounded-lg bg-primary-50 dark:!bg-dark-surface">
          <i class="pi pi-check-square text-primary-600"></i>
        </div>
        <span class="font-bold text-slate-800 dark:text-white text-base">
          Детали задачи #{{ store.selectedTask?.id }}
        </span>
      </div>
    </template>

    <!-- BODY (Scrollable) -->
    <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
      <!-- LOADING STATE -->
      <div v-if="store.isTaskLoading || !store.selectedTask" class="space-y-6">
        <Skeleton height="2.5rem" class="!bg-gray-100 dark:!bg-slate-800" />
        <div class="space-y-2">
          <Skeleton
            width="40%"
            height="1.2rem"
            class="!bg-gray-100 dark:!bg-slate-800"
          />
          <Skeleton height="8rem" class="!bg-gray-100 dark:!bg-slate-800" />
        </div>
      </div>

      <!-- CONTENT -->
      <div v-else class="flex flex-col gap-8 pb-20">
        <!-- Task Title Section -->
        <div class="group flex flex-col gap-1">
          <label
            class="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 ml-1"
            >Название</label
          >
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
              <div
                class="flex items-center gap-2 text-slate-800 dark:text-slate-200 font-bold text-sm"
              >
                <i class="pi pi-align-left text-slate-400"></i>
                Описание
              </div>
              <Textarea
                v-model="localDescription"
                rows="6"
                placeholder="Добавьте описание задачи (Markdown...)"
                class="w-full min-h-60 !bg-gray-50 dark:!bg-dark-bg/40 !border-gray-200 dark:!border-dark-border focus:!bg-white dark:focus:!bg-dark-bg focus:!ring-1 focus:!ring-primary-500 !text-slate-700 dark:!text-slate-300 !transition-colors !rounded-lg !p-3 !text-sm !leading-relaxed"
              />
              <div
                class="flex justify-between items-center text-[11px] text-slate-400"
              >
                <span class="flex items-center gap-1"
                  ><i class="pi pi-info-circle"></i> Markdown</span
                >
              </div>
            </div>
            <!-- Даты -->
            <div
              class="flex flex-col gap-1 mb-4 p-3 bg-gray-50 dark:bg-dark-bg/30 rounded-lg border border-gray-100 dark:border-dark-border"
            >
              <div class="flex justify-between text-[10px] text-slate-500">
                <span>Создано:</span>
                <span class="font-medium text-slate-700 dark:text-slate-300">{{
                  formatDate(store.selectedTask?.createdAt)
                }}</span>
              </div>
              <div class="flex justify-between text-[10px] text-slate-500">
                <span>Обновлено:</span>
                <span class="font-medium text-slate-700 dark:text-slate-300">{{
                  formatDate(store.selectedTask?.updatedAt)
                }}</span>
              </div>
            </div>
          </div>

          <!-- Sidebar Right -->
          <div class="lg:col-span-1 flex flex-col gap-6">
            <TaskSidebar
              v-model:assigneeId="localAssigneeId"
              v-model:priority="localPriority"
              v-model:tagIds="localTagIds"
            >
            </TaskSidebar>

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
    </div>

    <!-- FOOTER (Fixed) -->
    <template #footer>
      <div class="flex items-center justify-between w-full pt-2">
        <!-- Status Indicator -->
        <div
          class="flex items-center gap-2 text-xs transition-all duration-300 h-8"
        >
          <template v-if="isSaving">
            <i class="pi pi-spin pi-spinner text-primary-500"></i>
            <span class="text-slate-500 dark:text-slate-400"
              >Сохранение...</span
            >
          </template>
          <template v-else-if="lastSavedAt">
            <i class="pi pi-check text-green-500"></i>
            <span class="text-slate-500 dark:text-slate-400">
              Изменения сохранены
              <span class="text-slate-400 text-[10px]"
                >({{ lastSavedTime }})</span
              >
            </span>
          </template>
        </div>

        <!-- Actions -->
        <div class="flex gap-2">
          <Button
            label="Закрыть"
            text
            severity="secondary"
            size="small"
            @click="onClose"
          />
          <Button
            label="Сохранить"
            icon="pi pi-check"
            size="small"
            class="!bg-primary-600 !border-none !text-white !font-bold"
            :loading="isSaving"
            @click="saveAllAndClose"
          />
        </div>
      </div>
    </template>
  </Drawer>
</template>

<style scoped>
/* Скроллбар в стиле дашборда */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  @apply bg-transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  @apply bg-gray-200 dark:bg-slate-700 rounded-full;
}

:deep(.p-inputtext:focus) {
  box-shadow: none !important;
}

.flex-col {
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
