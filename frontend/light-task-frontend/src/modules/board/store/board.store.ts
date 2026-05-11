import { defineStore } from 'pinia';
import { ref, computed, reactive } from 'vue';
import { apiClient } from '@/api/config';
import { withClientMutationId } from '@/modules/realtime/lib/mutation-id';
import { getPlural } from '@/utils/plural';
import {
  TaskPriority,
  type ColumnRead,
  type ProjectRead,
  type TaskRead,
  type TaskMove,
  type TaskUpdate,
  type ColumnUpdate,
  type ColumnCreate,
  type TaskCreate,
  type ProjectMemberRead,
  type TagRead,
  type InvitationCreate,
  type ProjectUpdate,
  type InvitationRead,
  type TagCreate,
  type TagUpdate,
} from '@/api/client';

type RealtimeProjectEvent = {
  eventType: string;
  projectId?: number | null;
  clientMutationId?: string | null;
  payload: Record<string, any>;
};

interface BoardFilters {
  search: string;
  assigneeIds: number[];
  tagIds: number[];
  priorities: TaskPriority[];
}

export const useBoardStore = defineStore('board', () => {
  // --- STATE ---
  const project = ref<ProjectRead | null>(null);
  const columns = ref<ColumnRead[]>([]);
  const selectedTask = ref<TaskRead | null>(null);
  const taskDetailsById = ref<Record<number, TaskRead>>({});

  const members = ref<ProjectMemberRead[]>([]);
  const tags = ref<TagRead[]>([]);

  const activeColumnIdForTaskCreation = ref<number | null>(null);

  const isLoading = ref(false);
  const isTaskLoading = ref(false);
  const requestedTaskDetailsId = ref<number | null>(null);

  const activeInvitations = ref<InvitationRead[]>([]);
  const pendingMutationIds = ref<Set<string>>(new Set());
  const presenceByTaskId = ref<Record<number, { viewingUserIds: number[]; editingUserIds: number[] }>>({});
  const activeBoardUserCount = ref<number | null>(null);

  const filters = reactive<BoardFilters>({
    search: '',
    assigneeIds: [],
    tagIds: [],
    priorities: []
  });

  const isFilterActive = computed(() => {
    return (
      filters.search.trim().length > 0 ||
      filters.assigneeIds.length > 0 ||
      filters.tagIds.length > 0 ||
      filters.priorities.length > 0
    );
  });

  const activeBoardPresenceLabel = computed(() => {
    const count = Math.max(1, activeBoardUserCount.value ?? 1);
    return `${count} ${getPlural(count, ['на доске', 'на доске', 'на доске'])}`;
  });

  function canReadInvitations(): boolean {
    const role = project.value?.currentUserRole;
    return role === 'OWNER' || role === 'MANAGER';
  }

  async function refreshInvitationsIfAllowed(): Promise<void> {
    if (!project.value || !canReadInvitations()) return;
    try {
      await fetchInvitations();
    } catch {
      // Invitation refresh is best-effort for realtime UI consistency.
    }
  }

  function applyTaskSnapshot(task: TaskRead) {
    taskDetailsById.value = {
      ...taskDetailsById.value,
      [task.id]: task,
    };

    for (const col of columns.value) {
      if (!col.tasks) continue;
      const taskIndex = col.tasks.findIndex((item) => item.id === task.id);
      if (taskIndex !== -1) {
        col.tasks[taskIndex] = task;
        break;
      }
    }

    if (selectedTask.value?.id === task.id) {
      selectedTask.value = task;
    }
  }

  function rememberPendingMutation(mutationId: string) {
    pendingMutationIds.value.add(mutationId);
    window.setTimeout(() => {
      pendingMutationIds.value.delete(mutationId);
    }, 60_000);
  }

  function consumePendingMutation(mutationId?: string | null): boolean {
    if (!mutationId) return false;
    const found = pendingMutationIds.value.has(mutationId);
    if (found) {
      pendingMutationIds.value.delete(mutationId);
    }
    return found;
  }

  async function runMutation<T>(callback: () => Promise<T>): Promise<T> {
    return withClientMutationId(async (mutationId) => {
      rememberPendingMutation(mutationId);
      return callback();
    });
  }

  function upsertPresence(taskId: number, mode: 'viewing' | 'editing', userId: number, isActive: boolean) {
    const current = presenceByTaskId.value[taskId] ?? { viewingUserIds: [], editingUserIds: [] };
    const key = mode === 'viewing' ? 'viewingUserIds' : 'editingUserIds';
    const target = new Set(current[key]);
    if (isActive) {
      target.add(userId);
    } else {
      target.delete(userId);
    }
    presenceByTaskId.value = {
      ...presenceByTaskId.value,
      [taskId]: {
        ...current,
        [key]: [...target],
      },
    };
  }

  function applyPresenceSync(items: Array<{ taskId: number; viewingUserIds: number[]; editingUserIds: number[] }>) {
    const next: Record<number, { viewingUserIds: number[]; editingUserIds: number[] }> = {};
    for (const item of items) {
      next[item.taskId] = {
        viewingUserIds: item.viewingUserIds ?? [],
        editingUserIds: item.editingUserIds ?? [],
      };
    }
    presenceByTaskId.value = next;
  }

  function applyProjectPresence(payload: Record<string, any>) {
    if (typeof payload.activeUserCount !== 'number') return;
    activeBoardUserCount.value = Math.max(1, payload.activeUserCount);
  }

  function resetActiveBoardUserCount() {
    activeBoardUserCount.value = null;
  }

  const filteredColumns = computed(() => {
    if (!isFilterActive.value) {
      return columns.value;
    }

    const query = filters.search.toLowerCase().trim();

    return columns.value.map(col => ({
      ...col,
      tasks: (col.tasks || []).filter(task => {
        if (query) {
          const inTitle = task.title.toLowerCase().includes(query);
          const inDesc = (task as any).description?.toLowerCase().includes(query);

          if (!inTitle && !inDesc) return false;
        }

        if (filters.assigneeIds.length > 0) {
          if (!task.assigneeId) return false;
          if (!filters.assigneeIds.includes(task.assigneeId)) return false;
        }

        if (filters.tagIds.length > 0) {
          if (!task.tags || task.tags.length === 0) return false;
          const taskTagIds = task.tags.map(t => t.id);
          const hasTag = filters.tagIds.some(id => taskTagIds.includes(id));
          if (!hasTag) return false;
        }

        if (filters.priorities.length > 0) {
          if (!task.priority || !filters.priorities.includes(task.priority)) return false;
        }

        return true;
      })
    }));
  });

  // --- ACTIONS ---

  function resetFilters() {
    filters.search = '';
    filters.assigneeIds = [];
    filters.tagIds = [];
    filters.priorities = [];
  }

  function setActiveColumnForTaskCreation(columnId: number | null) {
    activeColumnIdForTaskCreation.value = columnId;
  }

  async function fetchBoard(projectId: number) {
    if (project.value?.id !== projectId) {
      selectedTask.value = null;
      taskDetailsById.value = {};
      requestedTaskDetailsId.value = null;
    }

    isLoading.value = true;
    try {
      const [projectData, columnsData, membersData, tagsData] = await Promise.all([
        apiClient.projects.getProjectDetailsApiProjectsProjectIdGet(projectId),
        apiClient.boards.getProjectBoardApiProjectsProjectIdColumnsGet(projectId),
        apiClient.projects.getProjectMembersApiProjectsProjectIdMembersGet(projectId),
        apiClient.tags.getProjectTagsApiProjectsProjectIdTagsGet(projectId)
      ]);
      project.value = projectData;
      columns.value = columnsData;
      members.value = membersData;
      tags.value = tagsData;
      presenceByTaskId.value = {};
      resetActiveBoardUserCount();
    } catch (error) {
      console.error('Ошибка загрузки доски:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchTaskDetails(taskId: number) {
    requestedTaskDetailsId.value = taskId;
    isTaskLoading.value = true;

    const cachedTask = taskDetailsById.value[taskId];
    if (cachedTask) {
      selectedTask.value = cachedTask;
    } else if (selectedTask.value?.id !== taskId) {
      selectedTask.value = null;
    }

    try {
      const task = await apiClient.boards.getTaskDetailsApiTasksTaskIdGet(taskId);
      taskDetailsById.value = {
        ...taskDetailsById.value,
        [taskId]: task,
      };

      if (requestedTaskDetailsId.value === taskId) {
        selectedTask.value = task;
      }
    } catch (error) {
      console.error('Ошибка загрузки задачи:', error);
      throw error;
    } finally {
      if (requestedTaskDetailsId.value === taskId) {
        isTaskLoading.value = false;
      }
    }
  }

  // --- COLUMNS ---

  async function createColumn(payload: ColumnCreate) {
    if (!project.value) return;
    try {
      const newCol = await runMutation(() =>
        apiClient.boards.createColumnApiProjectsProjectIdColumnsPost(project.value!.id, payload)
      );
      columns.value.push(newCol);
    } catch (error) {
      console.error('Ошибка создания колонки:', error);
      throw error;
    }
  }

  async function updateColumn(columnId: number, payload: ColumnUpdate) {
    if (!project.value) return;
    try {
      const updatedCol = await runMutation(() =>
        apiClient.boards.updateColumnApiProjectsProjectIdColumnsColumnIdPatch(
          project.value!.id,
          columnId,
          payload
        )
      );
      const index = columns.value.findIndex(c => c.id === columnId);
      if (index !== -1) {
        columns.value[index] = updatedCol;
      }
    } catch (error) {
      console.error('Ошибка обновления колонки:', error);
      throw error;
    }
  }

  async function deleteColumn(columnId: number) {
    if (!project.value) return;
    try {
      await runMutation(() =>
        apiClient.boards.deleteColumnApiProjectsProjectIdColumnsColumnIdDelete(project.value!.id, columnId)
      );
      columns.value = columns.value.filter(c => c.id !== columnId);
    } catch (error) {
      console.error('Ошибка удаления колонки:', error);
      throw error;
    }
  }

  async function moveColumn(newOrder: ColumnRead[]) {
    const oldColumns = [...columns.value];
    columns.value = newOrder;
    try {
      const ids = newOrder.map(c => c.id);
      await runMutation(() =>
        apiClient.boards.reorderColumnsApiProjectsProjectIdColumnsReorderPost(project.value!.id, {
          columnIds: ids
        })
      );
    } catch (error) {
      console.error('Ошибка перемещения колонки:', error);
      columns.value = oldColumns;
      throw error;
    }
  }

  // --- TASKS ---

  async function createTask(columnId: number, payload: TaskCreate) {
    if (!project.value) return;
    try {
      const newTask = await runMutation(() =>
        apiClient.boards.createTaskApiProjectsProjectIdColumnsColumnIdTasksPost(
          project.value!.id,
          columnId,
          payload
        )
      );

      taskDetailsById.value = {
        ...taskDetailsById.value,
        [newTask.id]: newTask,
      };

      const col = columns.value.find(c => c.id === columnId);
      if (col) {
        if (!col.tasks) col.tasks = [];
        col.tasks.push(newTask);
      }
    } catch (error) {
      console.error('Ошибка создания задачи:', error);
      throw error;
    }
  }


  async function updateTask(taskId: number, payload: TaskUpdate) {
    try {
      const updatedTask = await runMutation(() =>
        apiClient.boards.updateTaskApiTasksTaskIdPatch(taskId, payload)
      );

      if (selectedTask.value && selectedTask.value.id === taskId) {
        Object.assign(selectedTask.value, updatedTask);
      }

      taskDetailsById.value = {
        ...taskDetailsById.value,
        [taskId]: updatedTask,
      };

      for (const col of columns.value) {
        if (!col.tasks) continue;
        const taskIndex = col.tasks.findIndex(t => t.id === taskId);
        if (taskIndex !== -1) {
          col.tasks[taskIndex] = { ...col.tasks[taskIndex], ...updatedTask };
          break;
        }
      }
    } catch (error) {
      console.error('Ошибка обновления задачи:', error);
      throw error;
    }
  }


  async function deleteTask(taskId: number) {
    if (selectedTask.value?.id === taskId) {
      selectedTask.value = null;
    }

    const nextTaskDetails = { ...taskDetailsById.value };
    delete nextTaskDetails[taskId];
    taskDetailsById.value = nextTaskDetails;

    try {
      await runMutation(() =>
        apiClient.boards.deleteTaskApiTasksTaskIdDelete(taskId)
      );

      for (const col of columns.value) {
        if (!col.tasks) continue;
        const index = col.tasks.findIndex(t => t.id === taskId);
        if (index !== -1) {
          col.tasks.splice(index, 1);
          break;
        }
      }
    } catch (error) {
      console.error('Ошибка удаления задачи:', error);
      throw error;
    }
  }



  async function moveTask(
    taskId: number,
    targetColumnId: number,
    newIndexInColumn: number
  ) {
    try {
      const targetCol = columns.value.find(c => c.id === targetColumnId);
      if (!targetCol) throw new Error('Целевая колонка не найдена');

      let afterTaskId: number | null = null;
      const tasks = targetCol.tasks || [];


      if (newIndexInColumn > 0) {
        const prevTask = tasks[newIndexInColumn - 1];

        if (prevTask && prevTask.id !== taskId) {
          afterTaskId = prevTask.id;
        } else if (prevTask && prevTask.id === taskId) {

          const prevPrev = tasks[newIndexInColumn - 2];
          if (prevPrev) afterTaskId = prevPrev.id;
        }
      }


      const payload: TaskMove = {
        newColumnId: targetColumnId,
        afterTaskId: afterTaskId
      };

      await runMutation(() =>
        apiClient.boards.moveTaskApiTasksTaskIdMovePatch(taskId, payload)
      );

    } catch (error) {
      console.error('Ошибка перемещения задачи:', error);

      if (project.value) {
        await fetchBoard(project.value.id);
      }
      throw error;
    }
  }

  async function createInvitation(payload: InvitationCreate) {
    if (!project.value) throw new Error('Project not loaded');

    try {
      const res = await runMutation(() =>
        apiClient.invitations.createInvitationApiProjectsProjectIdInvitePost(
          project.value!.id,
          payload
        )
      );

      if (res) {
        activeInvitations.value.unshift(res);
      }

      return res;
    } catch (error) {
      console.error('Ошибка создания приглашения:', error);
      throw error;
    }
  }

  async function acceptInvitation(token: string) {
    try {
      const res = await runMutation(() =>
        apiClient.invitations.acceptInvitationApiInvitationsTokenAcceptPost(token)
      );
      return res;
    } catch (error) {
      console.error('Ошибка принятия приглашения:', error);
      throw error;
    }
  }

  // --- INVITATIONS ACTIONS ---
  async function fetchInvitations() {
    if (!project.value) return;
    try {
      activeInvitations.value = await apiClient.invitations.getProjectInvitationsApiProjectsProjectIdInvitationsGet(project.value.id);
    } catch (error) {
      console.error('Ошибка загрузки приглашений:', error)
    }
  }

  async function deleteInvitation(invitationId: number) {
    if (!project.value) return;
    try {
      await runMutation(() =>
        apiClient.invitations.deleteInvitationApiProjectsProjectIdInvitationsInvitationIdDelete(
          project.value!.id,
          invitationId
        )
      );
      activeInvitations.value = activeInvitations.value.filter(i => i.id !== invitationId);
    } catch (error) {
      console.error('Ошибка удаления приглашения:', error);
      throw error;
    }
  }

  async function updateProject(payload: ProjectUpdate) {
    if (!project.value) return;
    try {
      const updated = await runMutation(() =>
        apiClient.projects.updateProjectApiProjectsProjectIdPatch(project.value!.id, payload)
      );
      project.value = updated;
    } catch (error) {
      console.error('Ошибка обновления проекта:', error);
      throw error;
    }
  }

  async function deleteProject() {
    if (!project.value) return;
    try {
      await runMutation(() =>
        apiClient.projects.deleteProjectApiProjectsProjectIdDelete(project.value!.id)
      );
      // После удаления уходим на список проектов
    } catch (error) {
      console.error('Ошибка удаления проекта:', error);
      throw error;
    }
  }

  async function updateMemberRole(userId: number, role: any) {
    if (!project.value) return;
    try {
      const updatedMember = await runMutation(() =>
        apiClient.projects.updateMemberRoleApiProjectsProjectIdMembersUserIdPatch(
          project.value!.id,
          userId,
          { role }
        )
      );
      const index = members.value.findIndex(m => m.user.id === userId);
      if (index !== -1) members.value[index] = updatedMember;
    } catch (error) {
      console.error('Ошибка смены роли:', error);
      throw error;
    }
  }

  async function removeMember(userId: number) {
    if (!project.value) return;
    try {
      await runMutation(() =>
        apiClient.projects.removeProjectMemberApiProjectsProjectIdMembersUserIdDelete(project.value!.id, userId)
      );
      members.value = members.value.filter(m => m.user.id !== userId);
    } catch (error) {
      console.error('Ошибка удаления участника:', error);
      throw error;
    }
  }


  async function createTag(payload: TagCreate) {
    if (!project.value) return;
    try {
      const newTag = await runMutation(() =>
        apiClient.tags.createTagApiProjectsProjectIdTagsPost(project.value!.id, payload)
      );
      tags.value.push(newTag);
    } catch (error) {
      console.error('Ошибка создания тега:', error);
      throw error;
    }
  }

  async function updateTag(tagId: number, payload: TagUpdate) {
    try {
      const updated = await runMutation(() =>
        apiClient.tags.updateTagApiTagsTagIdPatch(tagId, payload)
      );
      const index = tags.value.findIndex(t => t.id === tagId);
      if (index !== -1) {
        tags.value[index] = updated;
      }
    } catch (error) {
      console.error('Ошибка обновления тега:', error);
      throw error;
    }
  }

  async function deleteTag(tagId: number) {
    try {
      await runMutation(() =>
        apiClient.tags.deleteTagApiTagsTagIdDelete(tagId)
      );
      tags.value = tags.value.filter(t => t.id !== tagId);
    } catch (error) {
      console.error('Ошибка удаления тега:', error);
      throw error;
    }
  }

  async function applyProjectScopeEvent(event: RealtimeProjectEvent) {
    if (!project.value) return;
    if (event.projectId && event.projectId !== project.value.id) return;

    if (consumePendingMutation(event.clientMutationId)) {
      return;
    }

    switch (event.eventType) {
      case 'project.updated':
        if (event.payload?.project) {
          project.value = event.payload.project as ProjectRead;
        }
        return;
      case 'task.updated':
        if (event.payload?.task) {
          applyTaskSnapshot(event.payload.task as TaskRead);
          return;
        }
        await fetchBoard(project.value.id);
        return;
      case 'invitation.created':
      case 'invitation.deleted':
        await refreshInvitationsIfAllowed();
        return;
      case 'member.added':
        await fetchBoard(project.value.id);
        await refreshInvitationsIfAllowed();
        return;
      case 'project.deleted':
        clearState();
        return;
      case 'task.viewing.started':
        upsertPresence(event.payload.taskId, 'viewing', event.payload.userId, true);
        return;
      case 'task.viewing.stopped':
        upsertPresence(event.payload.taskId, 'viewing', event.payload.userId, false);
        return;
      case 'task.editing.started':
        upsertPresence(event.payload.taskId, 'editing', event.payload.userId, true);
        return;
      case 'task.editing.stopped':
        upsertPresence(event.payload.taskId, 'editing', event.payload.userId, false);
        return;
      case 'task.presence.sync':
        applyPresenceSync(event.payload.items ?? []);
        return;
      case 'project.presence.sync':
      case 'project.presence.changed':
        applyProjectPresence(event.payload);
        return;
      default:
        await fetchBoard(project.value.id);
        return;
    }
  }

  function getTaskPresence(taskId: number) {
    return presenceByTaskId.value[taskId] ?? {
      viewingUserIds: [],
      editingUserIds: [],
    };
  }

  function getEditingUsers(taskId: number): number[] {
    return getTaskPresence(taskId).editingUserIds;
  }

  function getViewingUsers(taskId: number): number[] {
    return getTaskPresence(taskId).viewingUserIds;
  }


  function clearState() {
    project.value = null;
    columns.value = [];
    selectedTask.value = null;
    taskDetailsById.value = {};
    requestedTaskDetailsId.value = null;
    isTaskLoading.value = false;
    presenceByTaskId.value = {};
    resetActiveBoardUserCount();
  }

  return {
    project,
    columns,
    members,
    tags,
    selectedTask,
    taskDetailsById,
    activeInvitations,
    activeColumnIdForTaskCreation,
    isLoading,
    isTaskLoading,
    activeBoardUserCount,
    activeBoardPresenceLabel,
    fetchBoard,
    fetchTaskDetails,
    createColumn,
    updateColumn,
    deleteColumn,
    moveColumn,
    createTask,
    updateTask,
    deleteTask,
    moveTask,
    setActiveColumnForTaskCreation,
    createInvitation,
    acceptInvitation,
    clearState,
    updateProject,
    deleteProject,
    updateMemberRole,
    removeMember,
    fetchInvitations,
    deleteInvitation,
    createTag,
    updateTag,
    deleteTag,
    filters,
    filteredColumns,
    isFilterActive,
    resetFilters,
    applyProjectScopeEvent,
    consumePendingMutation,
    pendingMutationIds,
    presenceByTaskId,
    getTaskPresence,
    getEditingUsers,
    getViewingUsers,
    resetActiveBoardUserCount,
  };
});
