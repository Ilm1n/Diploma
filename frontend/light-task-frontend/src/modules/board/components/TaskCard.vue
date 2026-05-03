<script setup lang="ts">
import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import type { TaskPreview } from '@/api/client';
import Tag from 'primevue/tag';
import { useBoardStore } from '../store/board.store';
import UserAvatar from "@/shared/ui/UserAvatar.vue";
import { useAuthStore } from '@/modules/auth/store/auth.store';

const props = defineProps<{
  task: TaskPreview;
}>();

const store = useBoardStore();
const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const assignedMember = computed(() =>
    store.members.find(m => m.user.id === props.task.assigneeId)
);

const avatarUrl = computed(() => assignedMember.value?.user.avatarUrl);
const initials = computed(() => assignedMember.value?.user.username?.slice(0, 1).toUpperCase() || '?');

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
    case 'MEDIUM':
      return { severity: 'info', label: 'Medium', icon: 'pi pi-minus' };
    default:
      return null;
  }
});

const deadlineConfig = computed(() => {
  if (!props.task.deadlineAt) return null;

  const deadline = new Date(props.task.deadlineAt);
  if (Number.isNaN(deadline.getTime())) return null;

  const today = new Date();
  const startOfToday = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate(),
  );
  const startOfDeadline = new Date(
    deadline.getFullYear(),
    deadline.getMonth(),
    deadline.getDate(),
  );

  const diffDays = Math.round(
    (startOfDeadline.getTime() - startOfToday.getTime()) / 86_400_000,
  );
  const dateLabel = deadline.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
  });

  if (diffDays < 0) {
    return {
      label: dateLabel,
      class: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20',
    };
  }

  if (diffDays === 0) {
    return {
      label: 'Сегодня',
      class: 'text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20',
    };
  }

  return {
    label: dateLabel,
    class: 'text-slate-500 dark:text-slate-300 bg-slate-100 dark:bg-slate-700/60',
  };
});

const presence = computed(() => store.getTaskPresence(props.task.id));
const editingOthersCount = computed(() => {
  const currentUserId = authStore.user?.id;
  return (presence.value.editingUserIds ?? []).filter(id => id !== currentUserId).length;
});
const viewingOthersCount = computed(() => {
  const currentUserId = authStore.user?.id;
  return (presence.value.viewingUserIds ?? []).filter(id => id !== currentUserId).length;
});

</script>

<template>
  <div
      @click="openTask"
      class="task-card bg-white dark:bg-slate-800 p-3 rounded-lg border border-gray-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-all cursor-grab active:cursor-grabbing group relative select-none"
  >
    <button
        class="absolute top-2 right-2 p-1 rounded hover:bg-gray-200 dark:hover:bg-slate-600 text-slate-500 dark:text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity z-10 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm"
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
      <div
        v-if="editingOthersCount > 0 || viewingOthersCount > 0"
        class="mt-1.5 flex items-center gap-2 text-[10px] font-semibold text-amber-600 dark:text-amber-400"
      >
        <i class="pi pi-eye"></i>
        <span v-if="editingOthersCount > 0">{{ editingOthersCount }} редактируют</span>
        <span v-else>{{ viewingOthersCount }} просматривают</span>
      </div>
      <div
        v-if="deadlineConfig"
        class="mt-2 inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-bold"
        :class="deadlineConfig.class"
      >
        <i class="pi pi-calendar text-[10px]"></i>
        <span>{{ deadlineConfig.label }}</span>
      </div>
    </div>

    <!-- Footer: Priority & Assignee -->
    <div
      v-if="priorityConfig || task.assigneeId"
      class="flex items-center justify-between mt-auto"
    >
      <!-- Priority Badge -->
      <Tag
          v-if="priorityConfig"
          :value="priorityConfig.label"
          :severity="(priorityConfig.severity as any)"
          class="!text-[10px] !px-2 !py-0.5 !h-5 !font-bold"
      >
        <template #icon>
          <i :class="[priorityConfig.icon, 'text-[10px] mr-1']"></i>
        </template>
      </Tag>

      <!-- Assignee Avatar -->
      <div v-if="task.assigneeId" class="flex ml-auto">
        <UserAvatar
            class="!w-6 !h-6 !text-[10px] "
            :image="avatarUrl || undefined"
            :label="avatarUrl ? undefined : initials"
        />
      </div>
    </div>
  </div>
</template>
