<script
    setup
    lang="ts"
>
import {ref} from 'vue';
import {useForm} from 'vee-validate';
import {toTypedSchema} from '@vee-validate/zod';
import * as z from 'zod';
import {useProjectsStore} from '../store/projects.store';
import {useToast} from 'primevue/usetoast';

// UI
import Dialog from 'primevue/dialog';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Button from 'primevue/button';
import ColorPicker from 'primevue/colorpicker'; // <--- Новый компонент

defineProps<{
  visible: boolean;
}>();

const emit = defineEmits(['update:visible']);

const store = useProjectsStore();
const toast = useToast();

// Дефолтный цвет
const selectedColor = ref('3B82F6');

const schema = toTypedSchema(z.object({
  name: z.string().min(1, 'Название обязательно').max(100),
  description: z.string().optional(),
}));

const {defineField, handleSubmit, errors, isSubmitting, resetForm} = useForm({
  validationSchema: schema
});

const [name, nameAttrs] = defineField('name');
const [description, descriptionAttrs] = defineField('description');

const onSubmit = handleSubmit(async (values) => {
  try {
    await store.createProject({
      name: values.name,
      description: values.description || null,
      color: '#' + selectedColor.value
    });

    toast.add({severity: 'success', summary: 'Проект создан', life: 3000});
    emit('update:visible', false);
    resetForm();
    selectedColor.value = '3B82F6';
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: 'Ошибка',
      detail: 'Не удалось создать проект',
      life: 3000
    });
  }
});
</script>

<template>
  <Dialog
      :visible="visible"
      @update:visible="emit('update:visible', $event)"
      modal
      header="Новый проект"
      :style="{ width: '450px' }"
      :draggable="false"
      class="p-dialog-custom !w-[95vw] md:!w-[850px]"
  >
    <!-- Убрали все классы цветов из Dialog, оставили только логику -->

    <form
        @submit="onSubmit"
        class="flex flex-col gap-6 mt-2"
    >

      <!-- Name -->
      <div class="flex flex-col gap-2">
        <label
            for="p-name"
            class="font-bold text-base text-slate-800 dark:text-white"
        >
          Название проекта
        </label>
        <InputText
            id="p-name"
            v-model="name"
            v-bind="nameAttrs"
            :invalid="!!errors.name"
            placeholder="Например: Redesign 2025"
            class="w-full !p-3"
        />
        <small
            class="text-red-500 font-medium"
            v-if="errors.name"
        >{{ errors.name }}</small>
      </div>

      <!-- Description -->
      <div class="flex flex-col gap-2">
        <label
            for="p-desc"
            class="font-bold text-base text-slate-800 dark:text-white"
        >
          Описание
        </label>
        <Textarea
            id="p-desc"
            v-model="description"
            v-bind="descriptionAttrs"
            rows="3"
            placeholder="Краткое описание целей..."
            class="w-full resize-none !p-3"
        />
      </div>

      <!-- Color Picker -->
      <div class="flex flex-col gap-3">
        <label class="font-bold text-base text-slate-800 dark:text-white">
          Цвет обложки
        </label>
        <!-- Здесь вручную задаем цвета, так как это div -->
        <div class="flex items-center gap-4 p-3 border border-gray-200 dark:border-slate-700 rounded-xl bg-gray-50 dark:bg-slate-900">
          <ColorPicker
              v-model="selectedColor"
              format="hex"
          />

          <span class="font-mono text-slate-600 dark:text-slate-300 uppercase font-medium">
            #{{ selectedColor }}
          </span>

          <div
              class="ml-auto px-3 py-1 rounded-md text-xs font-bold text-white shadow-sm"
              :style="{ backgroundColor: '#' + selectedColor }"
          >
            Preview
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-3 mt-4 pt-4 border-t border-gray-100 dark:border-slate-700">
        <Button
            type="button"
            label="Отмена"
            text
            severity="secondary"
            @click="emit('update:visible', false)"
            class="!font-bold text-slate-600 dark:text-slate-300 hover:bg-gray-100 dark:hover:bg-slate-800"
        />
        <Button
            type="submit"
            label="Создать проект"
            icon="pi pi-check"
            :loading="isSubmitting"
            class="!bg-primary-600 hover:!bg-primary-700 !border-none !rounded-lg !px-6 !font-bold shadow-lg shadow-primary-500/20 !text-white"
        />
      </div>
    </form>
  </Dialog>
</template>

<style scoped>
:deep(.p-colorpicker-preview) {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.5rem;
  border: 2px solid #e2e8f0;
}

.dark :deep(.p-colorpicker-preview) {
  border-color: #475569;
}
</style>