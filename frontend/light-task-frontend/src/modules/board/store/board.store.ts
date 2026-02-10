import { defineStore } from 'pinia';
import { ref } from 'vue';
import { apiClient } from '@/api/config';
import type {
  ColumnRead,
  ProjectRead,
  TaskRead,
  TaskMove,
  TaskUpdate,
  ColumnUpdate,
  ColumnCreate,
  TaskCreate,
  ProjectMemberRead,
  TagRead,
} from '@/api/client';

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

  // --- ACTIONS ---

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
    clearState
  };
});