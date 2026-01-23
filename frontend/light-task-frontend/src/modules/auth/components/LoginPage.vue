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

// Русская схема валидации
const validationSchema = toTypedSchema(
    z.object({
      username: z.string({required_error: 'Введите имя пользователя'})
          .min(1, 'Имя пользователя обязательно'),
      password: z.string({required_error: 'Введите пароль'})
          .min(1, 'Пароль обязателен'),
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
    toast.add({severity: 'success', summary: 'С возвращением!', life: 3000});
    await router.push('/projects');
  } catch (error: any) {
    // Обработка ошибки
    let errorMsg = 'Неверные данные для входа';
    if (error.response?.data?.detail) {
      errorMsg = error.response.data.detail;
    }
    if (Array.isArray(errorMsg)) {
      errorMsg = errorMsg[0].msg || JSON.stringify(errorMsg);
    }

    toast.add({
      severity: 'error',
      summary: 'Ошибка входа',
      detail: errorMsg,
      life: 5000
    });
  }
});
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden transition-colors duration-300">

    <!-- Decorative Blobs -->
    <div class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-primary-500/20 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"></div>

    <!-- Theme Toggle -->
    <button
        @click="toggleTheme"
        class="absolute top-6 right-6 p-2 rounded-full hover:bg-gray-200 dark:hover:bg-dark-surface transition-colors z-20"
    >
      <i :class="isDark ? 'pi pi-sun text-yellow-400' : 'pi pi-moon text-slate-600'" style="font-size: 1.5rem"></i>
    </button>

    <!-- Login Card -->
    <div class="w-full max-w-md bg-white dark:bg-dark-surface rounded-2xl shadow-xl p-8 z-10 border border-gray-100 dark:border-dark-border transition-colors duration-300">

      <div class="text-center mb-8">
        <router-link to="/"><h1 class="text-3xl font-bold text-slate-800 dark:text-white mb-2 tracking-tight">LightTask</h1></router-link>
        <p class="text-slate-500 dark:text-slate-400">Войдите, чтобы управлять проектами</p>
      </div>

      <form @submit.prevent="onSubmit" class="space-y-4">

        <!-- Username -->
        <div>
          <label for="login-username" class="block text-base font-medium text-slate-700 dark:text-gray-200 mb-2">
            Имя пользователя
          </label>
          <InputText
              id="login-username"
              v-model="username"
              v-bind="usernameAttrs"
              :invalid="!!errors.username"
              autocomplete="username"
              class="w-full !p-3 !text-base"
              placeholder="Введите username"
          />
          <!-- FIX: Резервируем место под ошибку (min-h) -->
          <div class="min-h-[1.5rem] mt-1">
            <small class="text-red-500 transition-opacity duration-200" v-if="errors.username">
              {{ errors.username }}
            </small>
          </div>
        </div>

        <!-- Password -->
        <div>
          <label for="login-password" class="block text-base font-medium text-slate-700 dark:text-gray-200 mb-2">
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
              inputClass="w-full !p-3 !text-base"
              :inputProps="{ autocomplete: 'current-password' }"
          />
          <!-- FIX: Резервируем место под ошибку -->
          <div class="min-h-[1.5rem] mt-1">
            <small class="text-red-500 transition-opacity duration-200" v-if="errors.password">
              {{ errors.password }}
            </small>
          </div>
        </div>

        <!-- Submit -->
        <Button
            type="submit"
            label="Войти"
            :loading="isSubmitting"
            class="w-full !rounded-xl !bg-primary-600 hover:!bg-primary-700 !border-none !py-3.5 !text-base !font-semibold shadow-md shadow-primary-500/30 !text-white mt-2"
        />
      </form>

      <div class="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
        Нет аккаунта?
        <router-link
            to="/register"
            class="text-primary-600 dark:text-primary-400 hover:underline font-medium"
        >Регистрация
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.p-password .p-icon) {
  @apply text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300;
}
</style>