import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

import { apiClient } from '@/api/config';
import { useBoardStore } from './board.store';

describe('board project presence', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  it('updates active board user count from project presence events', async () => {
    const store = useBoardStore();
    store.project = { id: 1 } as any;

    await store.applyProjectScopeEvent({
      eventType: 'project.presence.sync',
      projectId: 1,
      payload: { projectId: 1, activeUserCount: 2 },
    });

    expect(store.activeBoardUserCount).toBe(2);
    expect(store.activeBoardPresenceLabel).toBe('2 на доске');
  });

  it('uses a local minimum presence label before realtime sync arrives', () => {
    const store = useBoardStore();
    store.project = { id: 1 } as any;

    expect(store.activeBoardPresenceLabel).toBe('1 на доске');
  });

  it('resets active board user count when board state clears', async () => {
    const store = useBoardStore();
    store.project = { id: 1 } as any;

    await store.applyProjectScopeEvent({
      eventType: 'project.presence.changed',
      projectId: 1,
      payload: { projectId: 1, activeUserCount: 5 },
    });
    store.clearState();

    expect(store.activeBoardUserCount).toBeNull();
  });
});

describe('board realtime reducers', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  it('applies task.moved locally without refetching board data', async () => {
    const getProjectDetails = vi.spyOn(apiClient.projects, 'getProjectDetailsApiProjectsProjectIdGet');
    const getColumns = vi.spyOn(apiClient.boards, 'getProjectBoardApiProjectsProjectIdColumnsGet');
    const getMembers = vi.spyOn(apiClient.projects, 'getProjectMembersApiProjectsProjectIdMembersGet');
    const getTags = vi.spyOn(apiClient.tags, 'getProjectTagsApiProjectsProjectIdTagsGet');
    const store = useBoardStore();
    const movedTask = {
      id: 10,
      title: 'Moved',
      projectId: 1,
      columnId: 2,
      position: 10,
      priority: 'MEDIUM',
      assigneeId: null,
      deadlineAt: null,
      tags: [],
      description: null,
      authorId: null,
      createdAt: '2026-01-01T00:00:00Z',
      updatedAt: '2026-01-01T00:00:01Z',
    } as any;

    store.project = { id: 1 } as any;
    store.columns = [
      {
        id: 1,
        projectId: 1,
        name: 'Todo',
        position: 1,
        tasksLimit: null,
        tasks: [{ ...movedTask, columnId: 1, position: 1 }],
      },
      {
        id: 2,
        projectId: 1,
        name: 'Done',
        position: 2,
        tasksLimit: null,
        tasks: [],
      },
    ];

    await store.applyProjectScopeEvent({
      eventType: 'task.moved',
      projectId: 1,
      payload: {
        task: movedTask,
        fromColumnId: 1,
        toColumnId: 2,
      },
    });

    expect(store.columns[0]!.tasks).toEqual([]);
    expect(store.columns[1]!.tasks?.map((task) => task.id)).toEqual([10]);
    expect(store.taskDetailsById[10]).toEqual(movedTask);
    expect(getProjectDetails).not.toHaveBeenCalled();
    expect(getColumns).not.toHaveBeenCalled();
    expect(getMembers).not.toHaveBeenCalled();
    expect(getTags).not.toHaveBeenCalled();
  });

  it('ignores realtime events for pending local mutations', async () => {
    const store = useBoardStore();
    const mutationId = 'local-mutation';

    store.project = { id: 1 } as any;
    store.pendingMutationIds.add(mutationId);
    store.columns = [
      {
        id: 1,
        projectId: 1,
        name: 'Todo',
        position: 1,
        tasksLimit: null,
        tasks: [
          {
            id: 10,
            title: 'Local',
            projectId: 1,
            columnId: 1,
            position: 1,
            tags: [],
          } as any,
        ],
      },
      {
        id: 2,
        projectId: 1,
        name: 'Done',
        position: 2,
        tasksLimit: null,
        tasks: [],
      },
    ];

    await store.applyProjectScopeEvent({
      eventType: 'task.moved',
      projectId: 1,
      clientMutationId: mutationId,
      payload: {
        task: {
          id: 10,
          title: 'Local',
          projectId: 1,
          columnId: 2,
          position: 1,
        },
        fromColumnId: 1,
        toColumnId: 2,
      },
    });

    expect(store.columns[0]!.tasks?.map((task) => task.id)).toEqual([10]);
    expect(store.columns[1]!.tasks).toEqual([]);
    expect(store.pendingMutationIds.has(mutationId)).toBe(true);
  });

  it('removes deleted tasks from columns, selected task and details cache', async () => {
    const store = useBoardStore();
    const task = {
      id: 10,
      title: 'Deleted',
      projectId: 1,
      columnId: 1,
      position: 1,
      tags: [],
    } as any;

    store.project = { id: 1 } as any;
    store.columns = [
      {
        id: 1,
        projectId: 1,
        name: 'Todo',
        position: 1,
        tasksLimit: null,
        tasks: [task],
      },
    ];
    store.selectedTask = task;
    store.taskDetailsById = { 10: task };

    await store.applyProjectScopeEvent({
      eventType: 'task.deleted',
      projectId: 1,
      payload: { taskId: 10, columnId: 1 },
    });

    expect(store.columns[0]!.tasks).toEqual([]);
    expect(store.selectedTask).toBeNull();
    expect(store.taskDetailsById[10]).toBeUndefined();
  });

  it('applies column reorder events locally', async () => {
    const store = useBoardStore();

    store.project = { id: 1 } as any;
    store.columns = [
      { id: 1, projectId: 1, name: 'A', position: 1, tasksLimit: null, tasks: [] },
      { id: 2, projectId: 1, name: 'B', position: 2, tasksLimit: null, tasks: [] },
      { id: 3, projectId: 1, name: 'C', position: 3, tasksLimit: null, tasks: [] },
    ];

    await store.applyProjectScopeEvent({
      eventType: 'columns.reordered',
      projectId: 1,
      payload: { columnOrder: [3, 1, 2] },
    });

    expect(store.columns.map((column) => column.id)).toEqual([3, 1, 2]);
  });
});
