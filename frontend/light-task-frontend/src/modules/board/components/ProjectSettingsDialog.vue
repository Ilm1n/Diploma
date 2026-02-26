<script setup lang="ts">
import { ref, watch } from 'vue';
import { useBoardStore } from '../store/board.store';
import { useRouter } from 'vue-router';
import { useToast } from 'primevue/usetoast';
import { useConfirm } from 'primevue/useconfirm';
import { ProjectRole } from '@/api/client';

import Dialog from 'primevue/dialog';
import Tabs from 'primevue/tabs';
import TabList from 'primevue/tablist';
import Tab from 'primevue/tab';
import TabPanels from 'primevue/tabpanels';
import TabPanel from 'primevue/tabpanel';
import InputText from 'primevue/inputtext';
import Textarea from 'primevue/textarea';
import Button from 'primevue/button';
import Select from 'primevue/select';
import ColorPicker from 'primevue/colorpicker';
import UserAvatar from '@/shared/ui/UserAvatar.vue';
import InviteMemberDialog from '@/modules/invitations/components/InviteMemberDialog.vue';
import InviteQrDialog from '@/modules/invitations/components/InviteQrDialog.vue';

const props = defineProps<{ visible: boolean }>();
const emit = defineEmits(['update:visible']);

const store = useBoardStore();
const router = useRouter();
const toast = useToast();
const confirm = useConfirm();

const isInviteDialogVisible = ref(false);
const qrLink = ref('');
const isQrVisible = ref(false);

const projectName = ref('');
const projectDesc = ref('');

const newTagName = ref('');
const newTagColor = ref('3b82f6');

watch(() => props.visible, (val) => {
  if (val && store.project) {
    projectName.value = store.project.name;
    projectDesc.value = store.project.description || '';
    store.fetchInvitations();
  } else {
    isInviteDialogVisible.value = false;
    isQrVisible.value = false;
  }
});

const saveGeneral = async () => {
  try {
    await store.updateProject({ name: projectName.value, description: projectDesc.value });
    toast.add({ severity: 'success', summary: 'Обновлено', detail: 'Настройки сохранены', life: 3000 });
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось сохранить' });
  }
};

const handleCreateTag = async () => {
  if (!newTagName.value.trim()) return;
  try {
    await store.createTag({
      name: newTagName.value,
      color: '#' + newTagColor.value
    });
    newTagName.value = '';
    toast.add({ severity: 'success', summary: 'Тег создан', life: 2000 });
  } catch (e) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось создать тег' });
  }
};

const confirmDeleteProject = () => {
  confirm.require({
    message: 'Это действие нельзя отменить. Все данные проекта будут удалены.',
    header: 'Удаление проекта',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Удалить навсегда',
    acceptClass: 'p-button-danger !text-white',
    rejectLabel: 'Отмена',
    rejectClass: '!text-white',
    accept: async () => {
      await store.deleteProject();
      await router.push('/projects');
    }
  });
};

const confirmRoleChange = (member: any, newRole: ProjectRole) => {
  const roleLabel = roleOptions.find(r => r.value === newRole)?.label;

  confirm.require({
    message: `Вы уверены, что хотите изменить роль пользователя ${member.user.username} на "${roleLabel}"?`,
    header: 'Подтверждение роли',
    icon: 'pi pi-user-edit',
    rejectLabel: 'Отмена',
    acceptLabel: 'Да',
    rejectClass: 'p-button-secondary p-button-outlined ',
    acceptClass: 'p-button-primary !text-white',
    accept: async () => {
      try {
        await store.updateMemberRole(member.user.id, newRole);
        toast.add({ severity: 'success', summary: 'Обновлено', detail: 'Роль успешно изменена', life: 3000 });
      } catch (e) {
        toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось изменить роль' });
      }
    },
    reject: () => {
      store.fetchBoard(store.project!.id);
    }
  });
};

const confirmRemoveMember = (member: any) => {
  confirm.require({
    message: `Удалить пользователя ${member.user.username} из проекта?`,
    header: 'Исключение участника',
    icon: 'pi pi-user-minus',
    acceptLabel: 'Удалить',
    rejectLabel: 'Нет',
    acceptClass: 'p-button-danger !text-white',
    rejectClass: 'p-button-primary !text-white',
    accept: async () => {
      await store.removeMember(member.user.id);
      toast.add({ severity: 'info', summary: 'Удален', detail: 'Участник покинул проект', life: 3000 });
    }
  });
};

const confirmDeleteInvitation = (invite: any) => {
  confirm.require({
    message: `Удалить приглашение?`,
    header: 'Удаление приглашения',
    icon: 'pi pi-link',
    acceptLabel: 'Удалить',
    rejectLabel: 'Нет',
    acceptClass: 'p-button-danger !text-white',
    rejectClass: 'p-button-primary !text-white',
    accept: async () => {
      await store.deleteInvitation(invite.id);
      toast.add({ severity: 'success', summary: 'Удалено', detail: 'Приглашение удалено', life: 3000 });
    }
  });
};

const openQr = (link: string) => {
  qrLink.value = link;
  isQrVisible.value = true;
};

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    toast.add({ severity: 'success', summary: 'Скопировано', detail: 'Ссылка скопирована в буфер обмена', life: 2000 });
  } catch (err) {
    toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Не удалось скопировать', life: 3000 });
  }
};

const roleOptions = [
  { label: 'Владелец', value: ProjectRole.OWNER },
  { label: 'Менеджер', value: ProjectRole.MANAGER },
  { label: 'Участник', value: ProjectRole.MEMBER }
];
</script>

<template>
  <Dialog
      :visible="visible"
      @update:visible="emit('update:visible', $event)"
      modal
      header="Настройки проекта"
      :contentStyle="{ minHeight: '550px' }"
      class="p-dialog-custom !w-[95vw] md:!w-[850px]"
      :draggable="false"
  >
    <Tabs value="general">
      <TabList class="overflow-x-auto whitespace-nowrap custom-scrollbar pb-1">
        <Tab value="general"><i class="pi pi-cog mr-2"></i>Общие</Tab>
        <Tab value="members"><i class="pi pi-users mr-2"></i>Участники</Tab>
        <Tab value="tags"><i class="pi pi-tags mr-2"></i>Теги</Tab>
        <Tab value="invites"><i class="pi pi-link mr-2"></i>Приглашения</Tab>
      </TabList>

      <TabPanels class="!px-0 sm:!px-4">
        <!-- ОБЩИЕ -->
        <TabPanel value="general">
          <div class="flex flex-col gap-6 py-6 max-w-2xl">
            <div class="flex flex-col gap-2">
              <label class="text-xs font-bold uppercase text-slate-400">Название</label>
              <InputText v-model="projectName" class="w-full" />
            </div>
            <div class="flex flex-col gap-2">
              <label class="text-xs font-bold uppercase text-slate-400">Описание</label>
              <Textarea v-model="projectDesc" rows="4" class="w-full" />
            </div>
            <div class="flex justify-end">
              <Button label="Сохранить" icon="pi pi-check" class="!bg-primary-600 !text-white" @click="saveGeneral" />
            </div>

            <div class="mt-12 p-6 border border-red-200 dark:border-red-900/30 bg-red-50 dark:bg-red-900/10 rounded-2xl">
              <h4 class="text-red-600 dark:text-red-400 font-bold mb-1">Удаление проекта</h4>
              <p class="text-xs  mb-4 !text-red-400">Будьте осторожны, это действие необратимо.</p>
              <Button label="Удалить проект..." severity="danger" outlined size="small" @click="confirmDeleteProject" />
            </div>
          </div>
        </TabPanel>

        <!-- УЧАСТНИКИ -->
        <TabPanel value="members">
          <div class="flex flex-col gap-3 py-4 sm:py-6">
            <div v-for="member in store.members" :key="member.id"
            class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-slate-50 dark:bg-dark-bg/40 rounded-2xl border border-slate-100 dark:border-dark-border">

            <div class="flex items-center gap-4">
              <UserAvatar :image="member.user.avatarUrl || undefined" :label="member.user.avatarUrl ? undefined : member.user.username[0]" size="md" />
              <div class="flex flex-col">
                <span class="font-bold text-sm">{{ member.user.username }}</span>
                <span class="text-[11px] text-slate-500 break-all">{{ member.user.email }}</span>
              </div>
            </div>

            <div class="flex items-center gap-2 sm:gap-4 w-full sm:w-auto">
              <Select
                  v-model="member.role"
                  :options="roleOptions"
                  optionLabel="label"
                  optionValue="value"
                  class="!text-xs !bg-transparent flex-1 sm:flex-none"
                  @change="confirmRoleChange(member, $event.value)"
                  :disabled="member.role === 'OWNER' || store.project?.currentUserRole !== 'OWNER'"
              />
              <Button
                  icon="pi pi-user-minus"
                  severity="danger"
                  text
                  rounded
                  class="shrink-0"
                  v-if="member.role !== 'OWNER' && store.project?.currentUserRole === 'OWNER'"
                  @click="confirmRemoveMember(member)"
              />
            </div>
          </div>
          </div>
        </TabPanel>

        <!-- ТЕГИ -->
        <TabPanel value="tags">
          <div class="flex flex-col gap-6 py-4 sm:py-6">
            <div class="flex flex-col sm:flex-row sm:items-end gap-3 p-4 bg-primary-50/50 dark:bg-dark-bg/40 rounded-2xl border border-primary-100 dark:border-dark-border">
              <div class="w-full sm:flex-1 flex flex-col gap-2">
                <label class="text-[10px] font-bold uppercase text-primary-600">Новый тег</label>
                <InputText v-model="newTagName" placeholder="Название тега..." class="w-full" @keydown.enter="handleCreateTag" />
              </div>
              <div class="flex items-center sm:items-end gap-3 w-full sm:w-auto mt-2 sm:mt-0">
                <div class="flex flex-col gap-2">
                  <label class="text-[10px] font-bold uppercase text-primary-600 hidden sm:block">Цвет</label>
                  <ColorPicker v-model="newTagColor" />
                </div>
                <Button icon="pi pi-plus" class="!bg-primary-600 dark:!text-white flex-1 sm:flex-none" @click="handleCreateTag" :disabled="!newTagName" />
              </div>
            </div>

            <!-- Список тегов -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div v-for="tag in store.tags" :key="tag.id"
                   class="flex items-center justify-between p-3 border border-slate-200 dark:border-dark-border rounded-xl">
                <div class="flex items-center gap-2">
                  <span class="w-3 h-3 rounded-full" :style="{ backgroundColor: tag.color }"></span>
                  <span class="text-sm font-medium">{{ tag.name }}</span>
                </div>
                <Button icon="pi pi-times" text severity="secondary" size="small" @click="store.deleteTag(tag.id)" />
              </div>
            </div>
          </div>
        </TabPanel>

        <!-- ПРИГЛАШЕНИЯ -->
        <TabPanel value="invites">
          <div class="flex flex-col gap-4 py-6">

            <div class="flex justify-between items-center mb-2">
              <h4 class="text-sm font-bold text-slate-700 dark:text-slate-300">Активные ссылки</h4>
              <Button
                  label="Создать ссылку"
                  icon="pi pi-plus"
                  size="small"
                  outlined
                  @click="isInviteDialogVisible = true"
              />
            </div>

            <div v-if="store.activeInvitations.length === 0" class="text-center py-12 text-slate-400">
              <i class="pi pi-link text-3xl mb-3"></i>
              <p>Активных ссылок пока нет</p>
            </div>

            <div v-for="invite in store.activeInvitations" :key="invite.id"
                 class="p-5 bg-slate-50 dark:bg-dark-bg/40 rounded-2xl border border-slate-100 dark:border-dark-border">
              <div class="flex justify-between items-center mb-4">
                <div class="flex items-center gap-2">
          <span class="px-2 py-0.5 rounded bg-primary-100 dark:bg-primary-900/40 text-primary-600 text-[10px] font-black uppercase">
            {{ invite.role }}
          </span>
                  <span v-if="invite.email" class="text-xs text-slate-500">для {{ invite.email }}</span>
                </div>
                <Button icon="pi pi-trash" severity="danger" text @click="confirmDeleteInvitation(invite)" />
              </div>

              <div class="flex gap-2 mb-3">
                <InputText
                    :value="invite.link"
                    readonly
                    class="flex-1 text-xs font-mono bg-white dark:bg-slate-800 border border-slate-200 dark:border-dark-border rounded-lg"
                />
                <Button
                    icon="pi pi-copy"
                    @click="copyToClipboard(invite.link)"
                    class="p-button-outlined"
                />
                <Button icon="pi pi-qrcode" severity="secondary" outlined @click="openQr(invite.link)" />
              </div>

              <div class="flex justify-between text-[10px] text-slate-400 font-bold uppercase tracking-widest">
                <span>Использовано: {{ invite.usedCount }} / {{ invite.maxUses || '∞' }}</span>
                <span>Истекает: {{ new Date(invite.expiresAt).toLocaleDateString() }}</span>
              </div>
            </div>
          </div>
        </TabPanel>
      </TabPanels>
    </Tabs>
    <InviteMemberDialog v-model:visible="isInviteDialogVisible" />
    <InviteQrDialog v-model:visible="isQrVisible" :value="qrLink" />
  </Dialog>
</template>

<style scoped>
:deep(.p-tabpanels) {
  @apply !bg-transparent;
}

:deep(.p-tabpanel) {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>