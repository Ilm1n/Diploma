<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from "vue";
import { useRouter } from "vue-router";
import { useBoardStore } from "../store/board.store";
import { VueDraggable } from "vue-draggable-plus";
import { useToast } from "primevue/usetoast";
import { useHead } from "@unhead/vue";
import { useDraggableScroll } from "@/composables/useDraggableScroll";
import {
  onClickOutside,
  useBreakpoints,
  breakpointsTailwind,
} from "@vueuse/core";

import Skeleton from "primevue/skeleton";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import BoardHeader from "../components/BoardHeader.vue";
import BoardColumn from "../components/BoardColumn.vue";
import TaskDetailDrawer from "../components/task-details/TaskDetailDrawer.vue";
import { getErrorMessage } from "@/utils/error";

const props = defineProps<{ projectId: string }>();
const store = useBoardStore();
const toast = useToast();

const isCreatingColumn = ref(false);
const newColumnName = ref("");
const createInput = ref();
const createColumnFormRef = ref(null);
const router = useRouter();

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

const startCreateColumn = () => {
  isCreatingColumn.value = true;
  setTimeout(() => createInput.value?.$el.focus(), 0);
};

const cancelCreateColumn = () => {
  isCreatingColumn.value = false;
  newColumnName.value = "";
};

onClickOutside(createColumnFormRef, () => {
  if (isCreatingColumn.value) cancelCreateColumn();
});

const saveColumn = async () => {
  if (!newColumnName.value.trim()) {
    cancelCreateColumn();
    return;
  }
  try {
    await store.createColumn({ name: newColumnName.value });
    cancelCreateColumn();
    await nextTick();
    if (scrollContainerRef.value) {
      scrollContainerRef.value.scrollTo({
        left: scrollContainerRef.value.scrollWidth,
        behavior: "smooth",
      });
    }
  } catch (e) {
    const errorMsg = getErrorMessage(e);
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: errorMsg,
      life: 3000,
    });
  }
};

const onColumnDragStart = () => {
  document.body.style.userSelect = "none";
  document.body.style.cursor = "grabbing";
};

const onColumnDrop = () => {
  document.body.style.userSelect = "";
  document.body.style.cursor = "";
  store.moveColumn(store.columns);
};

onMounted(() => {
  loadData();
});
onUnmounted(() => {
  store.clearState();
});
watch(
  () => props.projectId,
  () => {
    loadData();
  },
);

async function loadData() {
  const id = parseInt(props.projectId);
  if (isNaN(id)) {
    await router.push("/projects");
    return;
  }
  try {
    await store.fetchBoard(id);
  } catch (error) {
    const errorMsg = getErrorMessage(error);
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: errorMsg,
      life: 5000,
    });
    await router.push("/projects");
  }
}

const scrollContainerRef = ref<HTMLElement | null>(null);
useDraggableScroll(scrollContainerRef);

useHead({
  title: "Kantano - Доска",
  meta: [{ name: "robots", content: "noindex, nofollow" }],
});
</script>

<template>
  <div
    class="h-full flex flex-col bg-white dark:bg-dark-bg transition-colors duration-300"
  >
    <BoardHeader />

    <div
      id="board-scroll-container"
      ref="scrollContainerRef"
      class="flex-1 overflow-x-auto overflow-y-hidden bg-gray-100 dark:bg-[#0b1120] relative active:cursor-grabbing"
    >
      <div class="h-full flex items-start p-4 sm:p-6 pb-8 gap-4 sm:gap-6">
        <template v-if="store.isLoading && store.columns.length === 0">
          <div
            v-for="i in 3"
            :key="i"
            class="w-[280px] sm:w-80 h-full shrink-0"
          >
            <Skeleton
              height="100%"
              borderRadius="12px"
              class="!bg-gray-200 dark:!bg-slate-800"
            />
          </div>
        </template>

        <template v-else>
          <VueDraggable
            v-model="store.columns"
            :animation="150"
            :delay="100"
            group="columns"
            handle=".column-drag-handle"
            :delay-on-touch-only="true"
            :force-fallback="true"
            :fallback-tolerance="5"
            :fallback-on-body="true"
            :scroll="scrollContainerRef as any"
            :scroll-sensitivity="dragOptions.sensitivity"
            :scroll-speed="dragOptions.speed"
            :direction="'horizontal'"
            :disabled="store.isFilterActive"
            class="flex gap-4 sm:gap-6 h-full"
            ghost-class="column-ghost"
            drag-class="column-drag"
            fallback-class="column-fallback"
            @start="onColumnDragStart"
            @end="onColumnDrop"
          >
            <BoardColumn
              v-for="col in store.filteredColumns"
              :key="col.id"
              :column="col"
            />
          </VueDraggable>

          <!-- CREATE COLUMN BUTTON -->
          <div class="w-[280px] sm:w-80 shrink-0">
            <div
              v-if="isCreatingColumn"
              ref="createColumnFormRef"
              class="bg-gray-50 dark:bg-dark-surface p-3 rounded-xl border border-gray-200 dark:border-dark-border shadow-sm"
            >
              <InputText
                ref="createInput"
                v-model="newColumnName"
                placeholder="Название колонки..."
                class="w-full mb-2"
                @keydown.enter="saveColumn"
                @keydown.esc="cancelCreateColumn"
              />
              <div class="flex items-center gap-2">
                <Button
                  label="Добавить"
                  size="small"
                  class="!bg-primary-600 !border-none !text-white !text-xs !px-3 !py-2"
                  @click="saveColumn"
                />
                <Button
                  icon="pi pi-times"
                  text
                  rounded
                  size="small"
                  class="!text-slate-500 hover:!bg-gray-200 dark:hover:!bg-slate-700"
                  @click="cancelCreateColumn"
                />
              </div>
            </div>
            <button
              v-else
              @click="startCreateColumn"
              class="w-full py-3 rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 text-slate-500 hover:text-primary-600 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-slate-800/50 transition-all font-bold flex items-center justify-center gap-2"
            >
              <i class="pi pi-plus"></i> Добавить колонку
            </button>
          </div>
        </template>
      </div>
    </div>
    <TaskDetailDrawer />
  </div>
</template>

<style>
.column-ghost {
  @apply bg-slate-200 dark:bg-slate-800/50 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl;
  opacity: 0.5;
}
.column-ghost > * {
  visibility: hidden;
}

.column-drag {
  @apply rotate-2 scale-105 shadow-2xl cursor-grabbing opacity-100;
  pointer-events: none !important;
}
</style>
