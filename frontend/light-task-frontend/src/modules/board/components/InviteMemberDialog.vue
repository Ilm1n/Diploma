<script setup lang="ts">
import { ref } from 'vue';
import { useBoardStore } from '../store/board.store';
import { useToast } from 'primevue/usetoast';
import { ProjectRole } from '@/api/client';

// UI
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';
import SelectButton from 'primevue/selectbutton';
import InputText from 'primevue/inputtext';
// import InputNumber from 'primevue/inputnumber';
import Select from 'primevue/select';

defineProps<{ visible: boolean }>();
const emit = defineEmits(['update:visible']);

const store = useBoardStore();
const toast = useToast();

const isLoading = ref(false);
const invitationLink = ref('');

const selectedRole = ref(ProjectRole.MEMBER);
const targetEmail = ref('');
const expiresInDays = ref(7);
const maxUses = ref<number | null>(1);

const roleOptions = [
  { label: 'Участник', value: ProjectRole.MEMBER },
  { label: 'Менеджер', value: ProjectRole.MANAGER },
  { label: 'Владелец', value: ProjectRole.OWNER }

];

const expireOptions = [
  { label: '1 день', value: 1 },
  { label: '7 дней', value: 7 },
  { label: '30 дней', value: 30 }
];

const usageOptions = [
  { label: '1 раз', value: 1 },
  { label: '5 раз', value: 5 },
  { label: 'Безлимит', value: null }
];

const generateLink = async () => {
  isLoading.value = true;
  try {
    const res = await store.createInvitation({
      role: selectedRole.value,
      email: targetEmail.value.trim() || null,
      expiresInDays: expiresInDays.value,
      maxUses: maxUses.value
    });

    if (res && res.link) {
      invitationLink.value = res.link;
      toast.add({ severity: 'success', summary: 'Готово', detail: 'Ссылка создана', life: 2000 });
    }
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось создать ссылку', life: 3000 });
  } finally {
    isLoading.value = false;
  }
};

const copyToClipboard = async () => {
  if (!invitationLink.value) return;
  try {
    await navigator.clipboard.writeText(invitationLink.value);
    toast.add({ severity: 'success', summary: 'Скопировано', detail: 'Ссылка в буфере обмена', life: 2000 });
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось скопировать', life: 3000 });
  }
};

const close = () => {
  invitationLink.value = '';
  targetEmail.value = '';
  maxUses.value = 1;
  expiresInDays.value = 7;
  emit('update:visible', false);
};
</script>

<template>
  <Dialog
      :visible="visible"
      @update:visible="emit('update:visible', $event)"
      modal
      header="Пригласить в проект"
      :style="{ width: '500px' }"
      :draggable="false"
      class="p-dialog-custom"
      @hide="close"
  >
    <div class="flex flex-col gap-6 pt-2">

      <template v-if="!invitationLink">
        <!-- Роль -->
        <div class="flex flex-col gap-2">
          <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Роль нового участника</label>
          <SelectButton v-model="selectedRole" :options="roleOptions" optionLabel="label" optionValue="value" class="w-full" />
        </div>

        <!-- Email (Опционально) -->
        <div class="flex flex-col gap-2">
          <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Email (необязательно)</label>
          <InputText v-model="targetEmail" placeholder="example@mail.com" class="w-full" />
          <p class="text-[10px] text-slate-400">Только этот пользователь сможет принять приглашение</p>
        </div>

        <!-- Настройки времени и лимита -->
        <div class="grid grid-cols-2 gap-4">
          <div class="flex flex-col gap-2">
            <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Истекает через</label>
            <Select v-model="expiresInDays" :options="expireOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
          <div class="flex flex-col gap-2">
            <label class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Использований</label>
            <Select v-model="maxUses" :options="usageOptions" optionLabel="label" optionValue="value" class="w-full" />
          </div>
        </div>

        <Button
            label="Создать ссылку"
            icon="pi pi-link"
            class="w-full dark:!text-white !bg-primary-600 !border-none !py-3 !mt-2"
            :loading="isLoading"
            @click="generateLink"
        />
      </template>

      <template v-else>
        <div class="flex flex-col gap-4 py-4 text-center animate-fade-in">
          <div class="w-16 h-16 bg-green-50 dark:bg-green-900/20 text-green-500 rounded-full flex items-center justify-center mx-auto mb-2">
            <i class="pi pi-check text-2xl"></i>
          </div>
          <h3 class="font-bold text-xl">Ссылка готова!</h3>
          <p class="text-sm text-slate-500">Отправьте её коллеге. Она будет активна {{ expireOptions.find(o => o.value === expiresInDays)?.label }}.</p>

          <div class="flex gap-2 mt-4">
            <InputText :value="invitationLink" readonly class="flex-1 !bg-slate-50 dark:!bg-dark-bg" />
            <Button icon="pi pi-copy" @click="copyToClipboard" />
          </div>

          <Button label="Создать другое приглашение" text class="!mt-4 !text-xs" @click="invitationLink = ''" />
        </div>
      </template>

    </div>
  </Dialog>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>