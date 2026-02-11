<script setup lang="ts">
import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import type { TaskPreview } from '@/api/client';
import Avatar from 'primevue/avatar';
import Tag from 'primevue/tag';
import { useBoardStore } from '../store/board.store';

const props = defineProps<{
  task: TaskPreview;
}>();

const store = useBoardStore();
const router = useRouter();
const route = useRoute();

const assignedMember = computed(() =>
    store.members.find(m => m.user.id === props.task.assigneeId)
);

const avatarUrl = computed(() => assignedMember.value?.user.avatarUrl);
const initials = computed(() => assignedMember.value?.user.username?.slice(0, 2).toUpperCase() || '?');

const openTask = () => {
  router.push({ query: { ...route.query, taskId: props.task.id } });
};

const priorityConfig = computed(() => {
  switch (props.task.priority) {
    case 'CRITICAL':
      return { severity: 'danger', label: 'Critical', icon: 'pi pi-exclamation-triangle' };
    case 'HIGH':
      return { severity: 'warn', label: 'High', icon: 'pi pi-arrow-up' };
    case 'LOW':
      return { severity: 'success', label: 'Low', icon: 'pi pi-arrow-down' };
    default:
      return { severity: 'info', label: 'Medium', icon: 'pi pi-minus' };
  }
});

// const assigneeInitials = computed(() => {
//   return props.task.assigneeId ? String(props.task.assigneeId).slice(0, 2) : '?';
// });
</script>

<template>
  <div
      @click="openTask"
      class="task-card bg-white dark:bg-slate-800 p-3 rounded-lg border border-gray-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-all cursor-grab active:cursor-grabbing group relative select-none"
  >
    <button
        class="absolute top-2 right-2 p-1.5 rounded hover:bg-gray-200 dark:hover:bg-slate-600 text-slate-500 dark:text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity z-10 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm"
        aria-label="Редактировать"
        @click.stop="openTask"
    >
      <i class="pi pi-pencil text-xs"></i>
    </button>
    <!-- Tags Row -->
    <div v-if="task.tags && task.tags.length > 0" class="flex flex-wrap gap-1 mb-2">
      <span
          v-for="tag in task.tags"
          :key="tag.id"
          class="text-[10px] font-bold px-1.5 py-0.5 rounded text-white"
          :style="{ backgroundColor: tag.color || '#9CA3AF' }"
      >
        {{ tag.name }}
      </span>
    </div>

    <!-- Title -->
    <div class="mb-3">
      <h4 class="text-sm font-medium text-slate-800 dark:text-slate-100 leading-snug break-words">
        {{ task.title }}
      </h4>
    </div>

    <!-- Footer: Priority & Assignee -->
    <div class="flex items-center justify-between mt-auto">
      <!-- Priority Badge -->
      <Tag
          :value="priorityConfig.label"
          :severity="(priorityConfig.severity as any)"
          class="!text-[10px] !px-2 !py-0.5 !h-5 !font-bold"
      >
        <template #icon>
          <i :class="[priorityConfig.icon, 'text-[10px] mr-1']"></i>
        </template>
      </Tag>

      <!-- Assignee Avatar -->
      <div v-if="task.assigneeId" class="flex">
        <Avatar
            shape="circle"
            class="!w-6 !h-6 !text-[10px] !bg-primary-100 !text-primary-700 border border-white dark:border-slate-800"
            :image="avatarUrl || undefined"
            :label="avatarUrl ? undefined : initials"
        />
      </div>
    </div>
  </div>
</template>