<script setup lang="ts">
import { computed } from 'vue';
import Avatar from 'primevue/avatar';

interface Props {
  image?: string;
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
});

const sizeClass = computed(() => {
  switch (props.size) {
    case 'sm':
      return '!w-8 !h-8 text-sm';
    case 'lg':
      return '!w-12 !h-12 text-lg';
    default:
      return '!w-10 !h-10 text-base';
  }
});

const hasImage = computed(() => !!props.image);
</script>

<template>
  <Avatar
      :image="image"
      :label="label"
      shape="circle"
      :class="[
        sizeClass,
        hasImage ? '!bg-transparent' : '!bg-primary-100 dark:!bg-primary-900 !text-primary-600'
      ]"
  />
</template>