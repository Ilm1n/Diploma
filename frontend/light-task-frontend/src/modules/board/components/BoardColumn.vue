<script setup lang="ts">
import { ref, computed, nextTick } from "vue";
import type { ColumnRead } from "@/api/client";
import { useBoardStore } from "../store/board.store";
import { useConfirm } from "primevue/useconfirm";
import { useToast } from "primevue/usetoast";
import { getPlural } from "@/utils/plural";
import { VueDraggable } from "vue-draggable-plus";
import {
  breakpointsTailwind,
  onClickOutside,
  useBreakpoints,
} from "@vueuse/core";

import Button from "primevue/button";
import Menu from "primevue/menu";
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import TaskCard from "./TaskCard.vue";

const props = defineProps<{ column: ColumnRead }>();
const store = useBoardStore();
const confirm = useConfirm();
const toast = useToast();

const isRenaming = ref(false);
const newName = ref(props.column.name);
const nameInput = ref();

const breakpoints = useBreakpoints(breakpointsTailwind);
const isMobile = breakpoints.smaller("lg");

const dragOptions = computed(() => {
  if (isMobile.value) {
    return {
      sensitivity: 35,
      speed: 15,
    };
  }
  return {
    sensitivity: 120,
    speed: 40,
  };
});

const startRename = () => {
  newName.value = props.column.name;
  isRenaming.value = true;
  nextTick(() => nameInput.value?.$el?.focus());
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
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: "Не удалось переименовать",
      life: 3000,
    });
  }
};

const cancelRename = () => {
  isRenaming.value = false;
  newName.value = props.column.name;
};

const menu = ref();
const onMenuClick = (event: Event) => menu.value.toggle(event);

const items = [
  { label: "Переименовать", icon: "pi pi-pencil", command: startRename },
  { separator: true },
  {
    label: "Удалить",
    icon: "pi pi-trash",
    class: "text-red-500",
    command: () => {
      confirm.require({
        message: "Вы уверены, что хотите удалить эту колонку?",
        header: "Подтверждение",
        icon: "pi pi-info-circle",
        rejectLabel: "Отмена",
        acceptLabel: "Удалить",
        rejectClass: "p-button-secondary p-button-outlined",
        acceptClass: "p-button-danger !text-white",
        accept: async () => {
          await store.deleteColumn(props.column.id);
          toast.add({
            severity: "success",
            summary: "Удалено",
            detail: "Колонка удалена",
            life: 3000,
          });
        },
      });
    },
  },
];

const tasksCountLabel = computed(() => {
  const count = props.column.tasks?.length || 0;
  return `${count} ${getPlural(count, ["задача", "задачи", "задач"])}`;
});

const newTaskTitle = ref("");
const createTaskInput = ref();
const createFormRef = ref(null);

const isCreatingTask = computed(
  () => store.activeColumnIdForTaskCreation === props.column.id
);

const startCreateTask = () => {
  store.setActiveColumnForTaskCreation(props.column.id);
  nextTick(() => {
    createTaskInput.value?.$el?.focus();
    const container = document.getElementById(
      `column-tasks-${props.column.id}`
    );
    if (container) container.scrollTop = container.scrollHeight;
  });
};

const cancelCreateTask = () => {
  store.setActiveColumnForTaskCreation(null);
  newTaskTitle.value = "";
};

onClickOutside(createFormRef, () => {
  if (isCreatingTask.value) cancelCreateTask();
});

const saveTask = async () => {
  if (!newTaskTitle.value.trim()) {
    cancelCreateTask();
    return;
  }
  try {
    await store.createTask(props.column.id, { title: newTaskTitle.value });
    newTaskTitle.value = "";
    nextTick(() => {
      const container = document.getElementById(
        `column-tasks-${props.column.id}`
      );
      if (container) container.scrollTop = container.scrollHeight;
      createTaskInput.value?.$el?.focus();
    });
  } catch (e) {
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: "Не удалось создать задачу",
      life: 3000,
    });
  }
};

const tasksList = computed({
  get: () => props.column.tasks || [],
  set: (val) => {
    props.column.tasks = val;
  },
});

const onTaskDrop = async (event: any) => {
  const { to, item, newIndex } = event;
  const taskId = Number(item.dataset.taskId);
  const targetColumnId = Number(to.dataset.columnId);

  if (!taskId || !targetColumnId) return;

  try {
    await store.moveTask(taskId, targetColumnId, newIndex);
  } catch (e) {
    toast.add({
      severity: "error",
      summary: "Ошибка перемещения",
      detail: "Изменения отменены",
      life: 3000,
    });
  }
};
</script>

<template>
  <div
    class="w-[280px] sm:w-80 shrink-0 flex flex-col h-full max-h-[calc(100%-16px)]"
  >
    <div
      class="w-full max-h-full flex flex-col bg-gray-50 dark:bg-dark-surface rounded-xl border border-gray-200 dark:border-dark-border shadow-sm transition-colors duration-300"
    >
      <!-- HEADER -->
      <div
        class="column-drag-handle flex-none p-3 border-b border-gray-200 dark:border-dark-border/50 flex justify-between items-start gap-2 cursor-grab active:cursor-grabbing group"
      >
        <div v-if="!isRenaming" class="flex-1 min-w-0" @dblclick="startRename">
          <h3
            class="font-bold text-slate-700 dark:text-slate-200 truncate leading-6"
          >
            {{ column.name }}
          </h3>
          <span class="text-xs text-slate-400 font-medium">
            {{ tasksCountLabel }}
          </span>
        </div>

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

        <Button
          icon="pi pi-ellipsis-h"
          text
          rounded
          size="small"
          class="!w-8 !h-8 !text-slate-400 hover:!bg-gray-100 dark:hover:!bg-slate-700/50 hover:!text-slate-600 dark:hover:!text-slate-200 transition-opacity"
          @click="onMenuClick"
          aria-haspopup="true"
          aria-controls="column_menu"
        />
        <Menu ref="menu" id="column_menu" :model="items" :popup="true" />
      </div>

      <div
        :id="`column-tasks-${column.id}`"
        class="flex-1 overflow-y-auto min-h-0 p-2 custom-scrollbar"
      >
        <VueDraggable
          v-model="tasksList"
          group="tasks"
          :animation="150"
          :delay="100"
          :delay-on-touch-only="true"
          :force-fallback="true"
          :fallback-tolerance="5"
          :fallback-on-body="true"
          :scroll-sensitivity="dragOptions.sensitivity"
          :scroll-speed="dragOptions.speed"
          :disabled="store.isFilterActive"
          fallback-class="task-fallback"
          ghost-class="task-ghost"
          drag-class="task-drag"
          class="flex flex-col gap-2 min-h-[50px] pb-2"
          :data-column-id="column.id"
          @end="onTaskDrop"
        >
          <TaskCard
            v-for="task in tasksList"
            :key="task.id"
            :task="task"
            :data-task-id="task.id"
          />
        </VueDraggable>
      </div>

      <!-- FOOTER -->
      <div
        class="flex-none p-2 pt-0 bg-gray-50 dark:bg-dark-surface rounded-b-xl"
      >
        <div v-if="isCreatingTask" ref="createFormRef" class="mt-1">
          <div
            class="bg-white dark:bg-slate-800 p-2 rounded-lg border border-primary-500 shadow-sm"
          >
            <Textarea
              ref="createTaskInput"
              v-model="newTaskTitle"
              rows="2"
              autoResize
              placeholder="Что нужно сделать?"
              class="w-full !text-sm !bg-transparent !border-none !shadow-none !p-0 resize-none"
              @keydown.enter.prevent="saveTask"
              @keydown.esc="cancelCreateTask"
            />
            <div class="flex justify-between items-center mt-2">
              <Button
                label="Добавить карточку"
                size="small"
                class="!py-1.5 !px-3 !text-xs !bg-primary-600 !text-white !border-none !font-semibold"
                @click="saveTask"
              />
              <Button
                icon="pi pi-times"
                text
                rounded
                size="small"
                class="!w-7 !h-7 !text-slate-400 hover:!bg-slate-100 dark:hover:!bg-slate-700"
                @click="cancelCreateTask"
              />
            </div>
          </div>
        </div>

        <button
          v-else
          @click.stop="startCreateTask"
          class="w-full py-2 flex items-center justify-start px-2 gap-2 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-gray-200/50 dark:hover:bg-slate-700/50 rounded-lg transition-colors text-sm font-medium"
        >
          <i class="pi pi-plus"></i> Добавить карточку
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

.task-ghost {
  @apply bg-slate-200 dark:bg-slate-700 opacity-50 border-dashed border-2 border-slate-400;
}
.task-ghost > * {
  visibility: hidden;
}
.task-drag {
  @apply rotate-2 shadow-xl cursor-grabbing;
}
</style>
