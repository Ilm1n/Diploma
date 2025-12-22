// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/modules/auth/store/auth.store';

// Ленивая загрузка компонентов (Performance optimization)
const LoginPage = () => import('@/modules/auth/components/LoginPage.vue');
const ProjectsList = () => import('@/modules/projects/components/ProjectsList.vue');

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: ProjectsList,
      meta: { requiresAuth: true } // Эта страница защищена
    },
    {
      path: '/login',
      name: 'login',
      component: LoginPage,
      meta: { requiresAuth: false } // Публичная страница
    },
    // 404 можно добавить позже
  ]
});

// Global Navigation Guard
router.beforeEach(async (to, _, next) => {
  const authStore = useAuthStore();

  // Если мы еще не проверяли юзера (например, при перезагрузке страницы)
  // но у нас есть токен в localStorage — попробуем подгрузить юзера
  if (!authStore.user && authStore.accessToken) {
    try {
      await authStore.fetchUser();
    } catch (e) {
      // Если токен протух — стор сам сделает logout, но тут можно подстраховать
      return next('/login');
    }
  }

  // Проверка доступа
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Хочет на закрытую, но не залогинен -> на логин
    next('/login');
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    // Уже залогинен, но лезет на логин -> на главную
    next('/');
  } else {
    // Всё ок
    next();
  }
});

export default router;