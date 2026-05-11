import {defineStore} from 'pinia';
import {ref} from 'vue';
import {apiClient} from '@/api/config';
import type {ProjectRead, ProjectCreate} from '@/api/client';
import {
  hasPendingClientMutationId,
  rememberClientMutationId,
  withClientMutationId,
} from '@/modules/realtime/lib/mutation-id';

type RealtimeUserEvent = {
  eventType: string;
  clientMutationId?: string | null;
  payload?: Record<string, any>;
};

export const useProjectsStore = defineStore('projects', () => {
  // State
  const projects = ref<ProjectRead[]>([]);
  const isLoading = ref(false);
  const pendingMutationIds = ref<Set<string>>(new Set());

  function rememberPendingMutation(mutationId: string) {
    pendingMutationIds.value.add(mutationId);
    rememberClientMutationId(mutationId);
    window.setTimeout(() => {
      pendingMutationIds.value.delete(mutationId);
    }, 60_000);
  }

  function consumePendingMutation(mutationId?: string | null): boolean {
    if (!mutationId) return false;
    return pendingMutationIds.value.has(mutationId) || hasPendingClientMutationId(mutationId);
  }

  // Actions
  async function fetchProjects() {
    isLoading.value = true;
    try {
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
      const newProject = await withClientMutationId(async (mutationId) => {
        rememberPendingMutation(mutationId);
        return apiClient.projects.createProjectApiProjectsPost(payload, mutationId);
      });
      projects.value.unshift(newProject);
      return newProject;
    } catch (error) {
      console.error('Failed to create project', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function applyUserScopeEvent(event: RealtimeUserEvent) {
    if (consumePendingMutation(event.clientMutationId)) {
      return;
    }

    if (event.eventType === 'project.list_item_updated') {
      const projectId = event.payload?.projectId;
      const updatedAt = event.payload?.updatedAt;

      if (typeof projectId === 'number' && typeof updatedAt === 'string') {
        const index = projects.value.findIndex((project) => project.id === projectId);
        if (index !== -1) {
          projects.value[index] = {
            ...projects.value[index]!,
            updatedAt,
          };
          projects.value = [...projects.value].sort(
            (a, b) => Date.parse(b.updatedAt) - Date.parse(a.updatedAt),
          );
        }
      }
      return;
    }

    if (
      event.eventType === 'project.added_to_user' ||
      event.eventType === 'project.removed_from_user'
    ) {
      await fetchProjects();
    }
  }

  return {
    projects,
    isLoading,
    pendingMutationIds,
    fetchProjects,
    createProject,
    applyUserScopeEvent,
    consumePendingMutation,
  };
});
