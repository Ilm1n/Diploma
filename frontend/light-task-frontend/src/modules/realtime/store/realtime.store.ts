import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { API_BASE_URL } from '@/api/config/axios-instance';
import { useAuthStore } from '@/modules/auth/store/auth.store';
import { useBoardStore } from '@/modules/board/store/board.store';
import { useProjectsStore } from '@/modules/projects/store/projects.store';
import router from '@/router';

type RealtimeStatus = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'offline';

type RealtimeMessage = {
  type?: string;
  eventType?: string;
  projectId?: number | null;
  payload?: Record<string, any>;
  clientMutationId?: string | null;
};

const MAX_RECONNECT_DELAY_MS = 10_000;

export const useRealtimeStore = defineStore('realtime', () => {
  const userSocket = ref<WebSocket | null>(null);
  const projectSocket = ref<WebSocket | null>(null);

  const userStatus = ref<RealtimeStatus>('idle');
  const projectStatus = ref<RealtimeStatus>('idle');

  const currentProjectId = ref<number | null>(null);
  const userReconnectAttempt = ref(0);
  const projectReconnectAttempt = ref(0);

  const shouldKeepUserConnection = ref(false);
  const shouldKeepProjectConnection = ref(false);

  const isOffline = computed(() => !navigator.onLine);

  function wsBaseUrl(): string {
    if (API_BASE_URL) {
      return API_BASE_URL.replace(/^http/i, 'ws');
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}`;
  }

  function resetUserSocket() {
    if (userSocket.value) {
      userSocket.value.onopen = null;
      userSocket.value.onmessage = null;
      userSocket.value.onclose = null;
      userSocket.value.onerror = null;
      userSocket.value.close();
    }
    userSocket.value = null;
  }

  function resetProjectSocket() {
    if (projectSocket.value) {
      projectSocket.value.onopen = null;
      projectSocket.value.onmessage = null;
      projectSocket.value.onclose = null;
      projectSocket.value.onerror = null;
      projectSocket.value.close();
    }
    projectSocket.value = null;
  }

  function scheduleUserReconnect() {
    if (!shouldKeepUserConnection.value) return;
    const delay = Math.min(500 * (2 ** userReconnectAttempt.value), MAX_RECONNECT_DELAY_MS);
    userReconnectAttempt.value += 1;
    userStatus.value = isOffline.value ? 'offline' : 'reconnecting';
    window.setTimeout(async () => {
      const authStore = useAuthStore();
      if (!authStore.accessToken) {
        await authStore.restoreSession();
      }
      if (authStore.accessToken) {
        connectUser();
      }
    }, delay);
  }

  function scheduleProjectReconnect() {
    if (!shouldKeepProjectConnection.value || !currentProjectId.value) return;
    const delay = Math.min(500 * (2 ** projectReconnectAttempt.value), MAX_RECONNECT_DELAY_MS);
    projectReconnectAttempt.value += 1;
    projectStatus.value = isOffline.value ? 'offline' : 'reconnecting';
    window.setTimeout(async () => {
      const authStore = useAuthStore();
      if (!authStore.accessToken) {
        await authStore.restoreSession();
      }
      if (authStore.accessToken && currentProjectId.value) {
        connectProject(currentProjectId.value);
      }
    }, delay);
  }

  async function handleUserMessage(message: RealtimeMessage) {
    if (message.type === 'pong') return;
    if (!message.eventType) return;

    const projectsStore = useProjectsStore();
    const boardStore = useBoardStore();
    const authStore = useAuthStore();

    await projectsStore.applyUserScopeEvent({
      eventType: message.eventType,
      clientMutationId: message.clientMutationId,
    });

    if (
      message.eventType === 'project.removed_from_user' &&
      boardStore.project?.id === message.payload?.projectId
    ) {
      boardStore.clearState();
      if (router.currentRoute.value.name === 'project-board') {
        await router.push('/projects');
      }
    }

    if (message.eventType === 'project.added_to_user' && authStore.isAuthenticated) {
      await projectsStore.fetchProjects();
    }
  }

  async function handleProjectMessage(message: RealtimeMessage) {
    if (message.type === 'pong') return;
    if (!message.eventType) return;

    const authStore = useAuthStore();
    const boardStore = useBoardStore();
    await boardStore.applyProjectScopeEvent({
      eventType: message.eventType,
      projectId: message.projectId,
      clientMutationId: message.clientMutationId,
      payload: message.payload ?? {},
    });

    if (
      message.eventType === 'member.removed' &&
      message.payload?.userId === authStore.user?.id
    ) {
      boardStore.clearState();
      if (router.currentRoute.value.name === 'project-board') {
        await router.push('/projects');
      }
    }

    if (message.eventType === 'project.deleted') {
      boardStore.clearState();
      if (router.currentRoute.value.name === 'project-board') {
        await router.push('/projects');
      }
    }
  }

  function connectUser() {
    const authStore = useAuthStore();
    const token = authStore.accessToken;
    if (!token) {
      return;
    }

    shouldKeepUserConnection.value = true;
    resetUserSocket();
    userStatus.value = 'connecting';

    const socket = new WebSocket(`${wsBaseUrl()}/ws/user`);
    userSocket.value = socket;

    socket.onopen = () => {
      socket.send(JSON.stringify({ type: 'auth', accessToken: token }));
      const hadReconnect = userReconnectAttempt.value > 0;
      userReconnectAttempt.value = 0;
      userStatus.value = 'connected';
      if (hadReconnect) {
        const projectsStore = useProjectsStore();
        projectsStore.fetchProjects().catch(() => undefined);
      }
    };

    socket.onmessage = async (event) => {
      try {
        const message = JSON.parse(event.data) as RealtimeMessage;
        await handleUserMessage(message);
      } catch (error) {
        console.error('Failed to process user realtime message', error);
      }
    };

    socket.onerror = () => {
      userStatus.value = isOffline.value ? 'offline' : 'reconnecting';
    };

    socket.onclose = async () => {
      if (userSocket.value === socket) {
        userSocket.value = null;
      }
      if (!shouldKeepUserConnection.value) {
        userStatus.value = 'idle';
        return;
      }
      scheduleUserReconnect();
    };
  }

  function disconnectUser() {
    shouldKeepUserConnection.value = false;
    userStatus.value = 'idle';
    userReconnectAttempt.value = 0;
    resetUserSocket();
  }

  function connectProject(projectId: number) {
    const authStore = useAuthStore();
    const token = authStore.accessToken;
    if (!token) return;

    shouldKeepProjectConnection.value = true;
    currentProjectId.value = projectId;
    resetProjectSocket();
    projectStatus.value = 'connecting';

    const socket = new WebSocket(`${wsBaseUrl()}/ws/projects/${projectId}`);
    projectSocket.value = socket;

    socket.onopen = () => {
      socket.send(JSON.stringify({ type: 'auth', accessToken: token }));
      const hadReconnect = projectReconnectAttempt.value > 0;
      projectReconnectAttempt.value = 0;
      projectStatus.value = 'connected';
      if (hadReconnect) {
        const boardStore = useBoardStore();
        boardStore.fetchBoard(projectId).catch(() => undefined);
      }
    };

    socket.onmessage = async (event) => {
      try {
        const message = JSON.parse(event.data) as RealtimeMessage;
        await handleProjectMessage(message);
      } catch (error) {
        console.error('Failed to process project realtime message', error);
      }
    };

    socket.onerror = () => {
      projectStatus.value = isOffline.value ? 'offline' : 'reconnecting';
    };

    socket.onclose = () => {
      if (projectSocket.value === socket) {
        projectSocket.value = null;
      }
      if (!shouldKeepProjectConnection.value) {
        projectStatus.value = 'idle';
        return;
      }
      scheduleProjectReconnect();
    };
  }

  function disconnectProject() {
    shouldKeepProjectConnection.value = false;
    projectStatus.value = 'idle';
    projectReconnectAttempt.value = 0;
    currentProjectId.value = null;
    resetProjectSocket();
  }

  function sendProjectMessage(payload: Record<string, any>) {
    if (!projectSocket.value || projectSocket.value.readyState !== WebSocket.OPEN) {
      return;
    }
    projectSocket.value.send(JSON.stringify(payload));
  }

  return {
    userStatus,
    projectStatus,
    currentProjectId,
    isOffline,
    connectUser,
    disconnectUser,
    connectProject,
    disconnectProject,
    sendProjectMessage,
  };
});
