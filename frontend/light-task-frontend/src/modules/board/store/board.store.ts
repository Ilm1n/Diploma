import { defineStore } from 'pinia';
import { ref, computed, reactive } from 'vue';
import { apiClient } from '@/api/config';
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

  const members = ref<ProjectMemberRead[]>([]);
  const tags = ref<TagRead[]>([]);

  const activeColumnIdForTaskCreation = ref<number | null>(null);

  const isLoading = ref(false);
  const isTaskLoading = ref(false);

  const activeInvitations = ref<InvitationRead[]>([]);

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
    } catch (error) {
      console.error('Ошибка загрузки доски:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchTaskDetails(taskId: number) {
    isTaskLoading.value = true;
    selectedTask.value = null;
    try {
      const task = await apiClient.boards.getTaskDetailsApiTasksTaskIdGet(taskId);
      selectedTask.value = task;
    } catch (error) {
      console.error('Ошибка загрузки задачи:', error);
      throw error;
    } finally {
      isTaskLoading.value = false;
    }
  }

  // --- COLUMNS ---

  async function createColumn(payload: ColumnCreate) {
    if (!project.value) return;
    try {
      const newCol = await apiClient.boards.createColumnApiProjectsProjectIdColumnsPost(project.value.id, payload);
      columns.value.push(newCol);
    } catch (error) {
      console.error('Ошибка создания колонки:', error);
      throw error;
    }
  }

  async function updateColumn(columnId: number, payload: ColumnUpdate) {
    if (!project.value) return;
    try {
      const updatedCol = await apiClient.boards.updateColumnApiProjectsProjectIdColumnsColumnIdPatch(
        project.value.id,
        columnId,
        payload
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
      await apiClient.boards.deleteColumnApiProjectsProjectIdColumnsColumnIdDelete(project.value.id, columnId);
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
      await apiClient.boards.reorderColumnsApiProjectsProjectIdColumnsReorderPost(project.value!.id, {
        columnIds: ids
      });
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
      const newTask = await apiClient.boards.createTaskApiProjectsProjectIdColumnsColumnIdTasksPost(
        project.value.id,
        columnId,
        payload
      );


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
      const updatedTask = await apiClient.boards.updateTaskApiTasksTaskIdPatch(taskId, payload);

      if (selectedTask.value && selectedTask.value.id === taskId) {
        Object.assign(selectedTask.value, updatedTask);
      }

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

    try {
      await apiClient.boards.deleteTaskApiTasksTaskIdDelete(taskId);

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
      if (!targetCol) throw new Error('Target column not found');

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

      await apiClient.boards.moveTaskApiTasksTaskIdMovePatch(taskId, payload);

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
      const res = await apiClient.invitations.createInvitationApiProjectsProjectIdInvitePost(
        project.value.id,
        payload
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
      const res = await apiClient.invitations.acceptInvitationApiInvitationsTokenAcceptPost(token);
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
      console.error('Ошибка загрузки приглашений:', error);
    }
  }

  async function deleteInvitation(invitationId: number) {
    if (!project.value) return;
    try {
      await apiClient.invitations.deleteInvitationApiProjectsProjectIdInvitationsInvitationIdDelete(
        project.value.id,
        invitationId
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
      const updated = await apiClient.projects.updateProjectApiProjectsProjectIdPatch(project.value.id, payload);
      project.value = updated;
    } catch (error) {
      console.error('Ошибка обновления проекта:', error);
      throw error;
    }
  }

  async function deleteProject() {
    if (!project.value) return;
    try {
      await apiClient.projects.deleteProjectApiProjectsProjectIdDelete(project.value.id);
      // После удаления уходим на список проектов
    } catch (error) {
      console.error('Ошибка удаления проекта:', error);
      throw error;
    }
  }

  async function updateMemberRole(userId: number, role: any) {
    if (!project.value) return;
    try {
      const updatedMember = await apiClient.projects.updateMemberRoleApiProjectsProjectIdMembersUserIdPatch(
        project.value.id,
        userId,
        { role }
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
      await apiClient.projects.removeProjectMemberApiProjectsProjectIdMembersUserIdDelete(project.value.id, userId);
      members.value = members.value.filter(m => m.user.id !== userId);
    } catch (error) {
      console.error('Ошибка удаления участника:', error);
      throw error;
    }
  }


  async function createTag(payload: TagCreate) {
    if (!project.value) return;
    try {
      const newTag = await apiClient.tags.createTagApiProjectsProjectIdTagsPost(project.value.id, payload);
      tags.value.push(newTag);
    } catch (error) {
      console.error('Ошибка создания тега:', error);
      throw error;
    }
  }

  async function updateTag(tagId: number, payload: TagUpdate) {
    try {
      const updated = await apiClient.tags.updateTagApiTagsTagIdPatch(tagId, payload);
      const index = tags.value.findIndex(t => t.id === tagId);
      if (index !== -1) tags.value[index] = updated;
    } catch (error) {
      console.error('Ошибка обновления тега:', error);
      throw error;
    }
  }

  async function deleteTag(tagId: number) {
    try {
      await apiClient.tags.deleteTagApiTagsTagIdDelete(tagId);
      tags.value = tags.value.filter(t => t.id !== tagId);
    } catch (error) {
      console.error('Ошибка удаления тега:', error);
      throw error;
    }
  }


  function clearState() {
    project.value = null;
    columns.value = [];
    selectedTask.value = null;
  }

  return {
    project,
    columns,
    members,
    tags,
    selectedTask,
    activeInvitations,
    activeColumnIdForTaskCreation,
    isLoading,
    isTaskLoading,
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
  };
});