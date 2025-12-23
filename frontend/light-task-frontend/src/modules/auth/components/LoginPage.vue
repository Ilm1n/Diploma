<script
    setup
    lang="ts"
>
import {useAuthStore} from '../store/auth.store';
import {useRouter} from 'vue-router';
import {useToast} from 'primevue/usetoast';
import {useForm} from 'vee-validate';
import {toTypedSchema} from '@vee-validate/zod';
import * as z from 'zod';
import {useTheme} from '@/composables/useTheme';

import InputText from 'primevue/inputtext';
import Password from 'primevue/password';
import Button from 'primevue/button';

const authStore = useAuthStore();
const router = useRouter();
const toast = useToast();
const {isDark, toggleTheme} = useTheme();

const validationSchema = toTypedSchema(
    z.object({
      username: z.string().min(1, 'Введите имя пользователя'),
      password: z.string().min(1, 'Введите пароль'),
    })
);

const {defineField, handleSubmit, errors, isSubmitting} = useForm({
  validationSchema,
});

const [username, usernameAttrs] = defineField('username');
const [password, passwordAttrs] = defineField('password');

const onSubmit = handleSubmit(async (values) => {
  try {
    await authStore.login({
      username: values.username,
      password: values.password,
      grant_type: 'password',
    });
    toast.add({severity: 'success', summary: 'Welcome back!', life: 3000});
    await router.push('/');
  } catch (error: any) {
    const errorMsg = error.response?.data?.detail || 'Login failed';
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: Array.isArray(errorMsg) ? errorMsg[0].msg : errorMsg,
      life: 5000
    });
  }
});
</script>

<template>
  <!-- Main Container -->
  <div class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden transition-colors duration-300">

    <!-- Decorative Blobs -->
    <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary-500/20 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"></div>

    <!-- Theme Toggle -->
    <button
        @click="toggleTheme"
        class="absolute top-6 right-6 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-dark-surface transition-colors z-20"
    >
      <i
          :class="isDark ? 'pi pi-sun text-yellow-400' : 'pi pi-moon text-slate-600'"
          style="font-size: 1.5rem"
      ></i>
    </button>

    <!-- Login Card -->
    <div class="w-full max-w-md bg-white dark:bg-dark-surface rounded-2xl shadow-xl p-8 z-10 border border-gray-100 dark:border-dark-border transition-colors duration-300">

      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-slate-800 dark:text-white mb-2 tracking-tight">LightTask</h1>
        <p class="text-slate-500 dark:text-slate-400">Войдите, чтобы управлять проектами</p>
      </div>

      <form
          @submit="onSubmit"
          class="space-y-6"
      >

        <!-- Username -->
        <div class="space-y-2">
          <label
              for="login-username"
              class="block text-base font-medium text-slate-700 dark:text-gray-200"
          >
            Username
          </label>
          <InputText
              id="login-username"
              v-model="username"
              v-bind="usernameAttrs"
              :invalid="!!errors.username"
              autocomplete="username"
              class="w-full !p-3 !text-base !bg-gray-50 dark:!bg-slate-900 !border-gray-300 dark:!border-slate-600 focus:!border-primary-500 text-slate-900 dark:text-white placeholder:text-slate-400"
              placeholder="your_username"
          />
          <small
              class="text-red-500 block mt-1"
              v-if="errors.username"
          >{{ errors.username }}</small>
        </div>

        <!-- Password -->
        <div class="space-y-2">
          <label
              for="login-password"
              class="block text-base font-medium text-slate-700 dark:text-gray-200"
          >
            Пароль
          </label>
          <Password
              inputId="login-password"
              v-model="password"
              v-bind="passwordAttrs"
              :invalid="!!errors.password"
              :feedback="false"
              toggleMask
              placeholder="••••••••"
              class="w-full"
              inputClass="w-full !p-3 !text-base !bg-gray-50 dark:!bg-slate-900 !border-gray-300 dark:!border-slate-600 focus:!border-primary-500 text-slate-900 dark:text-white placeholder:text-slate-400"
              :inputProps="{ autocomplete: 'current-password' }"
          />
          <small
              class="text-red-500 block mt-1"
              v-if="errors.password"
          >{{ errors.password }}</small>
        </div>

        <!-- Submit -->
        <Button
            type="submit"
            label="Войти"
            :loading="isSubmitting"
            class="w-full !rounded-xl !bg-primary-600 hover:!bg-primary-700 !border-none !py-3.5 !text-base !font-semibold shadow-lg shadow-primary-500/30 transition-all hover:scale-[1.02]"
        />
      </form>

      <!-- Footer -->
      <div class="mt-8 text-center text-sm text-slate-500 dark:text-slate-400">
        Нет аккаунта?
        <a
            href="#"
            class="text-primary-600 dark:text-primary-400 hover:underline font-medium"
        >Регистрация
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.p-password .p-icon) {
  @apply text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300;
}
</style>