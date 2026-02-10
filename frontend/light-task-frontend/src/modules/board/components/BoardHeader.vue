<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useBoardStore } from '../store/board.store';
import AvatarGroup from 'primevue/avatargroup';
import Avatar from 'primevue/avatar';
import Button from 'primevue/button';
import Skeleton from 'primevue/skeleton';

const store = useBoardStore();
const router = useRouter();

const getInitials = (name: string) => name.charAt(0).toUpperCase();

const members = computed(() => [
  { id: 1, name: 'Alex', avatar: null },
  { id: 2, name: 'Marie', avatar: null },
]);

const goBack = () => {
  router.push('/projects');
};
</script>

<template>
  <div class="h-16 px-6 border-b border-gray-200 dark:border-dark-border bg-white dark:bg-dark-surface flex items-center justify-between shrink-0 transition-colors duration-300">

    <!-- LEFT: Back & Title -->
    <div class="flex items-center gap-4">
      <Button
          icon="pi pi-arrow-left"
          text
          rounded
          aria-label="Назад"
          class="!text-slate-500 hover:!bg-slate-100 dark:hover:!bg-slate-800"
          @click="goBack"
      />

      <div v-if="store.isLoading && !store.project" class="flex flex-col gap-1">
        <Skeleton width="8rem" height="1.5rem" />
        <Skeleton width="4rem" height="0.8rem" />
      </div>

      <div v-else-if="store.project">
        <h1 class="text-xl max-w-[20vw] truncate font-bold text-slate-800 dark:text-white leading-tight ">
          {{ store.project.name }}
        </h1>
        <div class="flex items-center gap-2 text-xs text-slate-500">
          <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: store.project.color }"></span>
          <span class="truncate flex-1 max-w-[20vw]">
            {{ store.project.description || 'Без описания' }}
          </span>
        </div>
      </div>
    </div>

    <!-- RIGHT: Members & Actions -->
    <div class="flex items-center gap-4">

      <!-- Team Avatars -->
      <AvatarGroup class="mr-2">
        <Avatar
            v-for="member in members.slice(0, 3)"
            :key="member.id"
            :label="getInitials(member.name)"
            shape="circle"
            class="!bg-primary-100 !text-primary-700  !border-solid !border-2 !border-white dark:!border-slate-800"
        />
        <Avatar
            v-if="members.length > 3"
            :label="`+${members.length - 3}`"
            shape="circle"
            class="!bg-gray-200 !text-slate-600 dark:!bg-slate-800 dark:!text-slate-100 !border-solid !border-2 !border-white dark:!border-slate-700 !text-xs"
        />
      </AvatarGroup>

      <!-- Settings (Only for Owner - logic later) -->
      <Button
          icon="pi pi-cog"
          text
          rounded
          class="!text-slate-400 hover:!bg-gray-100 dark:hover:!bg-slate-700/50 hover:!text-slate-600 dark:hover:!text-slate-200"
      />

      <!-- Invite Button -->
      <Button
          label="Share"
          icon="pi pi-user-plus"
          class="!bg-primary-600 hover:!bg-primary-700 dark:!text-white !border-none !text-sm !py-2 !px-4 !rounded-lg"
      />
    </div>
  </div>
</template>

<style scoped>
:deep(.p-avatar) {
  border-width: 1px !important;
}
</style>