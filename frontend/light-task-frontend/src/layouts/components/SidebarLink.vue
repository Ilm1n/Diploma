<!-- src/layouts/components/SidebarLink.vue -->
<script
    setup
    lang="ts"
>
import {computed} from 'vue';
import {useRoute} from 'vue-router';

const props = defineProps<{
  to: string;
  icon: string;
  label: string;
  collapsed: boolean;
}>();

const route = useRoute();
const isActive = computed(() => route.path === props.to);
</script>

<template>
  <router-link
      :to="to"
      class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden whitespace-nowrap"
      :class="[
      isActive
        ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 font-semibold'
        : 'text-slate-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-slate-200 font-medium',
      collapsed ? 'justify-center px-2' : ''
    ]"
  >
    <i
        :class="[
        icon,
        'text-lg transition-colors flex-shrink-0',
        isActive ? 'text-primary-600 dark:text-primary-400' : 'text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300'
      ]"
    ></i>

    <span
        class="transition-all duration-300 origin-left"
        :class="collapsed ? 'w-0 opacity-0 hidden' : 'w-auto opacity-100'"
    >
      {{ label }}
    </span>

    <div
        v-if="collapsed"
        class="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap"
    >
      {{ label }}
    </div>
  </router-link>
</template>