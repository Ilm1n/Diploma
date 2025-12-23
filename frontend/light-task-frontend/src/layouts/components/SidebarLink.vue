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
}>();

const route = useRoute();
const isActive = computed(() => route.path === props.to);
</script>

<template>
  <router-link
      :to="to"
      class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group"
      :class="[
      isActive
        ? 'bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400 font-semibold'
        : 'text-slate-600 dark:text-slate-400 hover:bg-gray-100 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-slate-200 font-medium'
    ]"
  >
    <i :class="[icon, 'text-lg transition-colors', isActive ? 'text-primary-600 dark:text-primary-400' : 'text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300']"></i>
    <span>{{ label }}</span>
  </router-link>
</template>