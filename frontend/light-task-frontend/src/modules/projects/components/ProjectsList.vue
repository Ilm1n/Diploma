<script
    setup
    lang="ts"
>
import {onMounted, ref} from 'vue';
import {useProjectsStore} from '../store/projects.store';
import ProjectCard from './ProjectCard.vue';
import CreateProjectCard from './CreateProjectCard.vue';
import CreateProjectDialog from './CreateProjectDialog.vue';
// import Button from 'primevue/button';
import Skeleton from 'primevue/skeleton';

const store = useProjectsStore();
const isCreateDialogOpen = ref(false);

onMounted(() => {
  store.fetchProjects();
});

const openCreateDialog = () => {
  isCreateDialogOpen.value = true;
};
</script>

<template>
  <div class="p-6 max-w-7xl mx-auto">

    <!-- Header -->
    <div class="flex justify-between items-center mb-8">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 dark:text-white">Мои проекты</h1>
        <p class="text-slate-500 dark:text-slate-400 mt-1">Управляйте задачами и командами</p>
      </div>

      <!-- Кнопка в хедере (Дублирующая) -->
      <!--            <Button-->
      <!--                label="Новый проект"-->
      <!--                icon="pi pi-plus"-->
      <!--                @click="openCreateDialog"-->
      <!--                class="!bg-primary-600 hover:!bg-primary-500 !border-none !rounded-xl !px-5 !py-2.5 !font-bold  transition-all hover:scale-105 active:scale-95"-->
      <!--            />-->
    </div>

    <!-- Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">

      <!-- Loading State -->
      <template v-if="store.isLoading && store.projects.length === 0">
        <Skeleton
            v-for="i in 4"
            :key="i"
            height="8rem"
            borderRadius="12px"
        />
      </template>

      <!-- Content -->
      <template v-else>
        <!-- 1. Карточка создания (в начале списка, как в Trello) -->
        <CreateProjectCard @click="openCreateDialog" />

        <!-- 2. Список проектов -->
        <ProjectCard
            v-for="project in store.projects"
            :key="project.id"
            :project="project"
        />
      </template>
    </div>

    <!-- Dialog -->
    <CreateProjectDialog v-model:visible="isCreateDialogOpen" />
  </div>
</template>