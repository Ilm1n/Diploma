<script
    setup
    lang="ts"
>
import {ref} from 'vue';
import {useAuthStore} from '@/modules/auth/store/auth.store';
import {useTheme} from '@/composables/useTheme';
import SidebarLink from '@/layouts/components/SidebarLink.vue';
import Avatar from 'primevue/avatar';

const authStore = useAuthStore();
const {isDark, toggleTheme} = useTheme();
const isMobileMenuOpen = ref(false);

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value;
};

// Меню навигации
const menuItems = [
  {label: 'Проекты', to: '/', icon: 'pi pi-th-large'},
];
</script>

<template>
  <div class="flex h-screen bg-gray-50 dark:bg-dark-bg transition-colors duration-300 font-sans">

    <!-- Mobile Overlay -->
    <div
        v-if="isMobileMenuOpen"
        class="fixed inset-0 bg-black/50 z-20 lg:hidden backdrop-blur-sm"
        @click="isMobileMenuOpen = false"
    ></div>

    <!-- SIDEBAR -->
    <aside
        class="fixed lg:static inset-y-0 left-0 z-30 w-72 bg-white dark:bg-dark-surface border-r border-gray-200 dark:border-dark-border transform transition-transform duration-300 lg:transform-none flex flex-col"
        :class="isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <!-- Logo Area -->
      <div class="h-20 flex items-center px-8 border-b border-gray-100 dark:border-dark-border/50">
        <i class="pi pi-bolt text-primary-500 text-2xl mr-3"></i>
        <span class="text-xl font-bold text-slate-800 dark:text-white tracking-tight">LightTask</span>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        <SidebarLink
            v-for="item in menuItems"
            :key="item.to"
            v-bind="item"
            @click="isMobileMenuOpen = false"
        />
      </nav>

      <!-- User Profile & Footer -->
      <div class="p-4 border-t border-gray-100 dark:border-dark-border/50 bg-gray-50/50 dark:bg-slate-800/50">

        <!-- Theme Toggle (Mini version) -->
        <div class="flex justify-between items-center mb-4 px-2">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Тема</span>
          <button
              @click="toggleTheme"
              class="text-slate-500 hover:text-primary-500 transition-colors"
          >
            <i :class="isDark ? 'pi pi-sun' : 'pi pi-moon'"></i>
          </button>
        </div>

        <!-- User Info -->
        <div
            class="flex items-center gap-3 p-2 rounded-xl hover:bg-white dark:hover:bg-slate-700 transition-colors cursor-pointer group"
        >
          <Avatar
              :image="authStore.user?.avatarUrl || undefined"
              :label="authStore.user?.avatarUrl ? undefined : authStore.user?.username?.charAt(0).toUpperCase()"
              class="bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-200"
              shape="circle"
              style="background-color: transparent;"
          />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-slate-700 dark:text-gray-200 truncate">
              {{ authStore.user?.username || authStore.user?.fullName }}
            </p>
            <p class="text-xs text-slate-500 dark:text-slate-400 truncate">
              {{ authStore.user?.email }}
            </p>
          </div>
          <button
              @click="authStore.logout"
              class="text-slate-400 hover:text-red-500 transition-colors"
          >
            <i class="pi pi-sign-out"></i>
          </button>
        </div>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="flex-1 flex flex-col min-w-0 overflow-hidden relative">

      <!-- Mobile Header -->
      <header
          class="lg:hidden h-16 bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border flex items-center px-4 justify-between shrink-0"
      >
        <div class="flex items-center gap-3">
          <button
              @click="toggleMobileMenu"
              class="text-slate-500 hover:text-slate-700 dark:text-slate-400"
          >
            <i class="pi pi-bars text-xl"></i>
          </button>
          <span class="font-bold text-slate-800 dark:text-white">LightTask</span>
        </div>
        <Avatar
            :image="authStore.user?.avatarUrl || undefined"
            :label="authStore.user?.avatarUrl ? undefined : authStore.user?.username?.charAt(0).toUpperCase()"
            shape="circle"
            class="!w-8 !h-8 bg-primary-100 text-primary-600"
        />
      </header>

      <!-- Scrollable Area -->
      <div class="flex-1 overflow-auto scroll-smooth">
        <!-- Контейнер для контента страниц -->
        <div class="h-full">
          <router-view />
        </div>
      </div>
    </main>
  </div>
</template>