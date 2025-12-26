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
      username: z.string({required_error: 'Обязательное поле'})
          .min(3, 'Минимум 3 символа')
          .max(50, 'Максимум 50 символов'),
      email: z.string({required_error: 'Обязательное поле'})
          .email('Введите корректный email'),
      password: z.string({required_error: 'Обязательное поле'})
          .min(8, 'Минимум 8 символов'),
      confirmPassword: z.string({required_error: 'Повторите пароль'})
    }).refine((data) => data.password === data.confirmPassword, {
      message: "Пароли не совпадают",
      path: ["confirmPassword"],
    })
);

const {defineField, handleSubmit, errors, isSubmitting} = useForm({
  validationSchema,
});

const [username, usernameAttrs] = defineField('username');
const [email, emailAttrs] = defineField('email');
const [password, passwordAttrs] = defineField('password');
const [confirmPassword, confirmPasswordAttrs] = defineField('confirmPassword');

const onSubmit = handleSubmit(async (values) => {
  try {
    await authStore.register({
      username: values.username,
      email: values.email,
      password: values.password,
    });

    toast.add({
      severity: 'success',
      summary: 'Аккаунт создан!',
      detail: 'Теперь войдите, используя свои данные',
      life: 5000
    });

    await router.push('/login');

  } catch (error: any) {
    let errorMsg = 'Ошибка регистрации';
    if (error.response?.data?.detail) {
      errorMsg = error.response.data.detail;
    }
    if (Array.isArray(errorMsg)) {
      errorMsg = errorMsg[0].msg || JSON.stringify(errorMsg);
    }

    toast.add({
      severity: 'error',
      summary: 'Ошибка',
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

    <!-- Register Card -->
    <div class="w-full max-w-md bg-white dark:bg-dark-surface rounded-2xl shadow-xl p-8 z-10 border border-gray-100 dark:border-dark-border transition-colors duration-300">

      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-slate-800 dark:text-white mb-2 tracking-tight">Регистрация</h1>
        <p class="text-slate-500 dark:text-slate-400">Создайте аккаунт в LightTask</p>
      </div>

      <form @submit.prevent="onSubmit" class="space-y-3">

        <!-- Username -->
        <div>
          <label for="reg-username" class="block text-base font-medium text-slate-700 dark:text-gray-200 mb-2">Имя пользователя</label>
          <InputText
              id="reg-username"
              v-model="username"
              v-bind="usernameAttrs"
              :invalid="!!errors.username"
              class="w-full !p-3"
              placeholder="ivan_ivanov"
          />
          <div class="min-h-[1.5rem] mt-1">
            <small class="text-red-500" v-if="errors.username">{{ errors.username }}</small>
          </div>
        </div>

        <!-- Email -->
        <div>
          <label for="reg-email" class="block text-base font-medium text-slate-700 dark:text-gray-200 mb-2">Email</label>
          <InputText
              id="reg-email"
              v-model="email"
              v-bind="emailAttrs"
              :invalid="!!errors.email"
              class="w-full !p-3"
              placeholder="example@mail.com"
          />
          <div class="min-h-[1.5rem] mt-1">
            <small class="text-red-500" v-if="errors.email">{{ errors.email }}</small>
          </div>
        </div>

        <!-- Password -->
        <div>
          <label for="reg-password" class="block text-base font-medium text-slate-700 dark:text-gray-200 mb-2">Пароль</label>
          <Password
              inputId="reg-password"
              v-model="password"
              v-bind="passwordAttrs"
              :invalid="!!errors.password"
              :feedback="false"
              toggleMask
              placeholder="••••••••"
              class="w-full"
              inputClass="w-full !p-3"
              promptLabel="Введите пароль"
              weakLabel="Слабый"
              mediumLabel="Средний"
              strongLabel="Надежный"
          />
          <div class="min-h-[1.5rem] mt-1">
            <small class="text-red-500" v-if="errors.password">{{ errors.password }}</small>
          </div>
        </div>

        <!-- Confirm Password -->
        <div>
          <label for="reg-confirm" class="block text-base font-medium text-slate-700 dark:text-gray-200 mb-2">Повторите пароль</label>
          <Password
              inputId="reg-confirm"
              v-model="confirmPassword"
              v-bind="confirmPasswordAttrs"
              :invalid="!!errors.confirmPassword"
              :feedback="false"
              toggleMask
              placeholder="••••••••"
              class="w-full"
              inputClass="w-full !p-3"
          />
          <div class="min-h-[1.5rem] mt-1">
            <small class="text-red-500" v-if="errors.confirmPassword">{{ errors.confirmPassword }}</small>
          </div>
        </div>

        <Button
            type="submit"
            label="Создать аккаунт"
            :loading="isSubmitting"
            class="w-full !rounded-xl !bg-primary-600 hover:!bg-primary-700 !border-none !py-3.5 !text-base !font-semibold shadow-md shadow-primary-500/30 !text-white mt-2"
        />
      </form>

      <!-- Footer -->
      <div class="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
        Уже есть аккаунт?
        <router-link
            to="/login"
            class="text-primary-600 dark:text-primary-400 hover:underline font-medium"
        >Войти
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