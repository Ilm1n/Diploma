<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { useBoardStore } from '../store/board.store';
import { VueDraggable } from 'vue-draggable-plus';
import { useToast } from 'primevue/usetoast';
import { useDraggableScroll } from '@/composables/useDraggableScroll';
import { onClickOutside } from '@vueuse/core';


// UI
import Skeleton from 'primevue/skeleton';
import Button from 'primevue/button';
import InputText from 'primevue/inputtext';
import ConfirmDialog from 'primevue/confirmdialog';
import BoardHeader from '../components/BoardHeader.vue';
import BoardColumn from '../components/BoardColumn.vue';

const props = defineProps<{ projectId: string }>();
const store = useBoardStore();
const route = useRoute();
const toast = useToast();

// --- Create Column Logic ---
const isCreatingColumn = ref(false);
const newColumnName = ref('');
const createInput = ref();
const createColumnFormRef = ref(null);

const startCreateColumn = () => {
  isCreatingColumn.value = true;
  setTimeout(() => createInput.value?.$el.focus(), 0);
};

const cancelCreateColumn = () => {
  isCreatingColumn.value = false;
  newColumnName.value = '';
};

onClickOutside(createColumnFormRef, () => {
  if (isCreatingColumn.value) {
    cancelCreateColumn();
  }
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
        behavior: 'smooth'
      });
    }

  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось создать колонку', life: 3000 });
  }
};

// --- DnD Events ---
const onColumnDragStart = () => {

  document.body.style.userSelect = 'none';
  document.body.style.cursor = 'grabbing';
};

const onColumnDrop = () => {

  document.body.style.userSelect = '';
  document.body.style.cursor = '';

  store.moveColumn(store.columns);
};

// --- Init ---
onMounted(() => { loadData(); });
onUnmounted(() => { store.clearState(); });
watch(() => props.projectId, () => { loadData(); });

async function loadData() {
  const id = parseInt(props.projectId);
  if (isNaN(id)) return;
  await store.fetchBoard(id);
  if (route.query.taskId) {
    const tId = parseInt(route.query.taskId as string);
    if (!isNaN(tId)) await store.fetchTaskDetails(tId);
  }
}


const scrollContainerRef = ref<HTMLElement | null>(null);
useDraggableScroll(scrollContainerRef);
</script>

<template>
  <div class="h-full flex flex-col bg-white dark:bg-dark-bg transition-colors duration-300">
    <BoardHeader />
    <ConfirmDialog />

    <div
        id="board-scroll-container"
        ref="scrollContainerRef"
        class="flex-1 overflow-x-auto overflow-y-hidden bg-gray-100 dark:bg-[#0b1120] relative active:cursor-grabbing"
    >
      <div class="h-full flex items-start p-6 gap-6">

        <!-- Loading -->
        <template v-if="store.isLoading && store.columns.length === 0">
          <div v-for="i in 3" :key="i" class="w-80 h-full shrink-0">
            <Skeleton height="100%" borderRadius="12px" class="!bg-gray-200 dark:!bg-slate-800" />
          </div>
        </template>

        <template v-else>

          <VueDraggable
              v-model="store.columns"
              :animation="150"
              group="columns"
              handle=".column-drag-handle"

              :force-fallback="true"
              :fallback-tolerance="3"

              :scroll="(scrollContainerRef as any)"
              :scroll-sensitivity="100"
              :scroll-speed="50"

              :direction="'horizontal'"

              class="flex gap-6 h-full items-start"

              ghost-class="column-ghost"
              drag-class="column-drag"

              @start="onColumnDragStart"
              @end="onColumnDrop"
          >
            <BoardColumn
                v-for="col in store.columns"
                :key="col.id"
                :column="col"
            />
          </VueDraggable>

          <!-- CREATE COLUMN BUTTON -->
          <div class="w-80 shrink-0">
            <div v-if="isCreatingColumn" ref="createColumnFormRef" class="bg-gray-50 dark:bg-dark-surface p-3 rounded-xl border border-gray-200 dark:border-dark-border shadow-sm">
              <InputText ref="createInput" v-model="newColumnName" placeholder="Название колонки..." class="w-full mb-2" @keydown.enter="saveColumn" @keydown.esc="cancelCreateColumn" />
              <div class="flex items-center gap-2">
                <Button label="Добавить" size="small" class="!bg-primary-600 !border-none !text-xs !px-3 !py-2" @click="saveColumn" />
                <Button icon="pi pi-times" text rounded size="small" class="!text-slate-500 hover:!bg-gray-200 dark:hover:!bg-slate-700" @click="cancelCreateColumn" />
              </div>
            </div>
            <button v-else @click="startCreateColumn" class="w-full py-3 rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 text-slate-500 hover:text-primary-600 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-slate-800/50 transition-all font-bold flex items-center justify-center gap-2">
              <i class="pi pi-plus"></i> Добавить колонку
            </button>
          </div>
        </template>

      </div>
    </div>
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