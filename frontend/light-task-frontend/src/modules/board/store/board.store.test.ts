import { beforeEach, describe, expect, it } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

import { useBoardStore } from './board.store';

describe('board project presence', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
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
