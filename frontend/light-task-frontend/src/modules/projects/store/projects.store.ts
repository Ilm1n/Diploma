import {defineStore} from 'pinia';
import {ref} from 'vue';
import {apiClient} from '@/api/config';
import type {ProjectRead, ProjectCreate} from '@/api/client';

export const useProjectsStore = defineStore('projects', () => {
  // State
  const projects = ref<ProjectRead[]>([]);
  const isLoading = ref(false);

  // Actions
  async function fetchProjects() {
    isLoading.value = true;
    try {
      // Генератор создал метод getMyProjectsApiProjectsGet
      const response = await apiClient.projects.getMyProjectsApiProjectsGet();
      projects.value = response;
    } catch (error) {
      console.error('Failed to fetch projects', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function createProject(payload: ProjectCreate) {
    isLoading.value = true;
    try {
      const newProject = await apiClient.projects.createProjectApiProjectsPost(payload);
      // Добавляем новый проект в начало списка локально (чтобы не перезагружать всё)
      projects.value.unshift(newProject);
      return newProject;
    } catch (error) {
      console.error('Failed to create project', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    projects,
    isLoading,
    fetchProjects,
    createProject
  };
});