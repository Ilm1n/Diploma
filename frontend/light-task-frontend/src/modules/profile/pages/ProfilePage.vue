<script setup lang="ts">
import { ref, computed } from "vue";
import { useAuthStore } from "@/modules/auth/store/auth.store";
import { useToast } from "primevue/usetoast";
import { getErrorMessage } from "@/utils/error";
import { useConfirm } from "primevue/useconfirm";
import { useForm } from "vee-validate";
import { toTypedSchema } from "@vee-validate/zod";
import * as z from "zod";
import { openCookieSettings } from "@/shared/consent/consent";

// UI
import InputText from "primevue/inputtext";
import Button from "primevue/button";
import UserAvatar from "@/shared/ui/UserAvatar.vue";

const authStore = useAuthStore();
const toast = useToast();
const confirm = useConfirm();
const fileInput = ref<HTMLInputElement | null>(null);

// --- 1. Avatar Logic ---
const avatarUrl = computed(() => authStore.user?.avatarUrl);
const currentEmail = computed(() => authStore.user?.email || "");
const userInitials = computed(
  () => authStore.user?.username?.slice(0, 1).toUpperCase() || "ME",
);

const triggerFileUpload = () => {
  fileInput.value?.click();
};

const onFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (!file) return;

  if (file.size > 5 * 1024 * 1024) {
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: "Файл слишком большой (макс 5MB)",
      life: 3000,
    });
    return;
  }

  try {
    await authStore.uploadAvatar(file);
    toast.add({
      severity: "success",
      summary: "Успешно",
      detail: "Аватар обновлен",
      life: 3000,
    });
  } catch (e) {
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: getErrorMessage(e),
      life: 3000,
    });
  } finally {
    if (fileInput.value) fileInput.value.value = "";
  }
};

// --- Delete Avatar Logic ---
const onDeleteAvatar = () => {
  confirm.require({
    message: "Вы уверены, что хотите удалить фото профиля?",
    header: "Удаление фото",
    icon: "pi pi-info-circle",
    rejectLabel: "Отмена",
    acceptLabel: "Удалить",
    rejectClass: "p-button-secondary p-button-outlined dark:!text-white",
    acceptClass: "p-button-danger !text-white",
    accept: async () => {
      try {
        await authStore.deleteAvatar();
        toast.add({
          severity: "success",
          summary: "Удалено",
          detail: "Фото профиля удалено",
          life: 3000,
        });
      } catch (e) {
        toast.add({
          severity: "error",
          summary: "Ошибка",
          detail: getErrorMessage(e),
          life: 3000,
        });
      }
    },
  });
};

// --- 2. Form Logic ---
const validationSchema = toTypedSchema(
  z.object({
    username: z.string().min(3, "Минимум 3 символа").max(50),
    fullName: z.string().max(255).optional().nullable(),
  }),
);

const { defineField, handleSubmit, errors, isSubmitting } = useForm({
  validationSchema,
  initialValues: {
    username: authStore.user?.username || "",
    fullName: authStore.user?.fullName || "",
  },
});

const [username, usernameAttrs] = defineField("username");
const [fullName, fullNameAttrs] = defineField("fullName");

const onSubmit = handleSubmit(async (values) => {
  try {
    const normalizedFullName =
      values.fullName && values.fullName.trim()
        ? values.fullName.trim()
        : null;

    await authStore.updateProfile({
      username: values.username,
      fullName: normalizedFullName,
    });
    toast.add({
      severity: "success",
      summary: "Сохранено",
      detail: "Данные профиля обновлены",
      life: 3000,
    });
  } catch (e) {
    toast.add({
      severity: "error",
      summary: "Ошибка",
      detail: getErrorMessage(e),
      life: 3000,
    });
  }
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <div class="mb-6 sm:mb-8">
      <h1 class="text-xl sm:text-2xl font-bold text-slate-800 dark:text-white">
        Настройки профиля
      </h1>
      <p class="text-sm sm:text-base text-slate-500 dark:text-slate-400">
        Управляйте личной информацией и безопасностью
      </p>
      <button
        type="button"
        class="mt-2 text-sm font-medium text-primary-600 hover:text-primary-700 hover:underline"
        @click="openCookieSettings"
      >
        Настройки cookie
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 sm:gap-8">
      <!-- LEFT COLUMN: Avatar -->
      <div class="md:col-span-1">
        <div
          class="bg-white dark:bg-dark-surface p-6 rounded-2xl border border-gray-200 dark:border-dark-border shadow-sm flex flex-col items-center text-center"
        >
          <div
            class="relative group cursor-pointer mb-4"
            @click="triggerFileUpload"
          >
            <UserAvatar
              :image="avatarUrl || undefined"
              :label="avatarUrl ? undefined : userInitials"
              shape="circle"
              class="!w-32 !h-32 !text-3xl !bg-primary-100 !text-primary-600 border-4 border-white dark:border-slate-700 shadow-lg"
            />

            <!-- Overlay on Hover -->
            <div
              class="absolute inset-0 bg-black/50 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            >
              <i class="pi pi-camera text-white text-2xl"></i>
            </div>
          </div>

          <h3 class="font-bold text-lg text-slate-800 dark:text-white">
            {{ authStore.user?.fullName || authStore.user?.username }}
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">
            {{ authStore.user?.email }}
          </p>

          <Button
            label="Изменить фото"
            size="small"
            outlined
            class="!w-full"
            @click="triggerFileUpload"
            :loading="authStore.isLoading"
          />

          <Button
            v-if="avatarUrl"
            label="Удалить фото"
            size="small"
            text
            severity="danger"
            class="!w-full !text-red-500 hover:!bg-red-50 dark:hover:!bg-red-900/20"
            icon="pi pi-trash"
            @click="onDeleteAvatar"
            :loading="authStore.isLoading"
          />

          <!-- Hidden File Input -->
          <input
            type="file"
            ref="fileInput"
            class="hidden"
            accept="image/png, image/jpeg, image/gif"
            @change="onFileSelect"
          />
        </div>
      </div>

      <!-- RIGHT COLUMN: Form -->
      <div class="md:col-span-2">
        <div
          class="bg-white dark:bg-dark-surface p-6 rounded-2xl border border-gray-200 dark:border-dark-border shadow-sm"
        >
          <h2
            class="text-lg font-bold text-slate-800 dark:text-white mb-6 border-b border-gray-100 dark:border-slate-700 pb-2"
          >
            Личные данные
          </h2>

          <form @submit.prevent="onSubmit" class="space-y-6">
            <!-- Username -->
            <div class="flex flex-col gap-2">
              <label
                for="username"
                class="font-medium text-slate-700 dark:text-slate-300"
                >Никнейм</label
              >
              <InputText
                id="username"
                v-model="username"
                v-bind="usernameAttrs"
                :invalid="!!errors.username"
                class="w-full"
              />
              <small class="text-red-500" v-if="errors.username">{{
                errors.username
              }}</small>
            </div>

            <!-- Full Name -->
            <div class="flex flex-col gap-2">
              <label
                for="fullname"
                class="font-medium text-slate-700 dark:text-slate-300"
                >Полное имя</label
              >
              <InputText
                id="fullname"
                v-model="fullName"
                v-bind="fullNameAttrs"
                placeholder="Иван Иванов"
                class="w-full"
              />
            </div>

            <!-- Email (Readonly) -->
            <div class="flex flex-col gap-2">
              <label
                for="email"
                class="font-medium text-slate-700 dark:text-slate-300"
                >Email</label
              >
              <InputText
                id="email"
                :model-value="currentEmail"
                disabled
                class="w-full !bg-gray-100 dark:!bg-slate-800 !text-slate-500"
              />
              <div
                class="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200"
              >
                Изменение email пока недоступно. Когда добавим отдельный безопасный
                flow, здесь появится управление адресом.
              </div>
            </div>

            <!-- Actions -->
            <div class="pt-4 flex justify-end">
              <Button
                type="submit"
                label="Сохранить изменения"
                icon="pi pi-check"
                :loading="isSubmitting"
                class="!bg-primary-600 dark:!text-white !border-none"
              />
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
