import {createRouter, createWebHistory} from 'vue-router';
import {useAuthStore} from '@/modules/auth/store/auth.store';

// Layouts
const AppLayout = () => import('@/layouts/components/AppLayout.vue');

// Pages
const LoginPage = () => import('@/modules/auth/components/LoginPage.vue');
const ProjectsList = () => import('@/modules/projects/components/ProjectsList.vue');

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginPage,
      meta: {requiresAuth: false}
    },
    {
      path: '/',
      component: AppLayout,
      meta: {requiresAuth: true},
      children: [
        {
          path: '', // path: '/' -> AppLayout -> ProjectsList
          name: 'home',
          component: ProjectsList,
        },
      ]
    },
  ]
});

router.beforeEach(async (to, _, next) => {
  const authStore = useAuthStore();
  if (!authStore.user && authStore.accessToken) {
    try {
      await authStore.fetchUser();
    } catch (e) {
      return next('/login');
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login');
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/');
  } else {
    next();
  }
});

export default router;