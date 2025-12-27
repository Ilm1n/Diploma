import {defineStore} from 'pinia';
import {ref} from 'vue';
import {apiClient} from '@/api/config';
import type {
  ColumnRead,
  ProjectRead,
  TaskPreview,
  TaskRead,
  TaskMove, ColumnUpdate, ColumnCreate
} from '@/api/client';

export const useBoardStore = defineStore('board', () => {
  // --- STATE ---
  const project = ref<ProjectRead | null>(null);
  const columns = ref<ColumnRead[]>([]);
  // Полная задача, открытая в Drawer
  const selectedTask = ref<TaskRead | null>(null);

  const isLoading = ref(false);
  const isTaskLoading = ref(false); // Лоадер для деталей задачи

  // --- ACTIONS ---

  /**
   * Загружает всю доску: инфо о проекте и колонки с задачами
   */
  async function fetchBoard(projectId: number) {
    isLoading.value = true;
    try {
      // Запускаем запросы параллельно для скорости
      const [projectData, columnsData] = await Promise.all([
        apiClient.projects.getProjectDetailsApiProjectsProjectIdGet(projectId),
        apiClient.boards.getProjectBoardApiProjectsProjectIdColumnsGet(projectId)
      ]);

      project.value = projectData;
      columns.value = columnsData;
    } catch (error) {
      console.error('Ошибка загрузки доски:', error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Загружает полные детали задачи (когда кликнули и открылся Drawer)
   */
  async function fetchTaskDetails(taskId: number) {
    isTaskLoading.value = true;
    selectedTask.value = null; // Сбрасываем старую
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

  /**
   * Перемещение колонки (Optimistic UI)
   */
  async function moveColumn(newOrder: ColumnRead[]) {
    // 1. Сохраняем бэкап на случай ошибки
    const oldColumns = [...columns.value];

    // 2. Применяем изменения сразу (локально)
    // Примечание: vue-draggable уже обновил массив columns через v-model,
    // но если мы вызываем этот метод вручную, то обновляем.
    columns.value = newOrder;

    try {
      // 3. Шлем запрос на бэк
      const ids = newOrder.map(c => c.id);
      await apiClient.boards.reorderColumnsApiProjectsProjectIdColumnsReorderPost(project.value!.id, {
        columnIds: ids
      });
    } catch (error) {
      // 4. ОШИБКА? Откатываемся назад!
      console.error('Ошибка перемещения колонки:', error);
      columns.value = oldColumns;
      throw error; // Пробрасываем ошибку, чтобы компонент показал Toast
    }
  }

  /**
   * Перемещение задачи (Самое сложное)
   * Вызывается ПОСЛЕ того, как vue-draggable визуально перенес задачу
   */
  async function moveTask(
    taskId: number,
    targetColumnId: number,
    newIndexInColumn: number,
    // Добавили _, чтобы TS не ругался
    _fromColumnId: number,
    _oldIndexInColumn: number,
    _movedTaskObj: TaskPreview
  ) {
    try {
      // 1. Вычисляем after_task_id
      const targetCol = columns.value.find(c => c.id === targetColumnId);
      if (!targetCol) throw new Error('Target column not found');

      let afterTaskId: number | null = null;

      // FIX: Гарантируем, что tasks - это массив
      const tasks = targetCol.tasks ?? [];

      if (newIndexInColumn > 0) {
        // Берем задачу, которая стоит ПЕРЕД текущей
        const prevTask = tasks[newIndexInColumn - 1];
        if (prevTask) {
          afterTaskId = prevTask.id;
        }
      }

      // 2. Отправляем запрос
      const payload: TaskMove = {
        newColumnId: targetColumnId,
        afterTaskId: afterTaskId
      };

      await apiClient.boards.moveTaskApiTasksTaskIdMovePatch(taskId, payload);

    } catch (error) {
      console.error('Ошибка перемещения задачи:', error);
      // При ошибке перезапрашиваем доску (самый надежный Rollback)
      if (project.value) {
        await fetchBoard(project.value.id);
      }
      throw error;
    }
  }

  async function createColumn(payload: ColumnCreate) {
    if (!project.value) return;
    try {
      // Бэкенд возвращает созданную колонку с ID
      const newCol = await apiClient.boards.createColumnApiProjectsProjectIdColumnsPost(project.value.id, payload);

      // Добавляем в конец списка локально
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

      // Обновляем локально
      const index = columns.value.findIndex(c => c.id === columnId);
      if (index !== -1) {
        // Сохраняем задачи, так как ответ updateColumn может вернуть пустой массив tasks (зависит от бэка),
        // но лучше перестраховаться и мерджить аккуратно.
        // В твоем API ColumnRead возвращает tasks, так что просто заменяем.
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

      // Удаляем из локального стейта
      columns.value = columns.value.filter(c => c.id !== columnId);
    } catch (error) {
      console.error('Ошибка удаления колонки:', error);
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
    selectedTask,
    isLoading,
    isTaskLoading,
    fetchBoard,
    fetchTaskDetails,
    moveColumn,
    moveTask,
    createColumn,
    updateColumn,
    deleteColumn,
    clearState
  };
});