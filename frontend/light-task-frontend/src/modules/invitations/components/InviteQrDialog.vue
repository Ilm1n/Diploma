<script setup lang="ts">
import { ref } from 'vue';
import QrcodeVue from 'qrcode.vue';
import Dialog from 'primevue/dialog';
import Button from 'primevue/button';

defineProps<{
  visible: boolean;
  value: string;
}>();

const emit = defineEmits(['update:visible']);

const qrContainerRef = ref<HTMLElement | null>(null);

const downloadQr = () => {
  const canvas = qrContainerRef.value?.querySelector('canvas');
  if (!canvas) return;

  const link = document.createElement('a');
  link.download = 'kantano-invite.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
};
</script>

<template>
  <Dialog
      :visible="visible"
      @update:visible="emit('update:visible', $event)"
      modal
      header="QR-код приглашения"
      class="p-dialog-custom !w-[350px]"
      :draggable="false"
  >
    <div class="flex flex-col items-center gap-6 py-4">

      <div ref="qrContainerRef" class="p-4 bg-white rounded-xl shadow-sm border border-slate-200">
        <QrcodeVue
            :value="value"
            :size="200"
            level="H"
            class="qr-canvas"
            render-as="canvas"
        />
      </div>

      <p class="text-center text-sm text-slate-500 dark:text-slate-400">
        Отсканируйте камерой телефона, чтобы присоединиться к проекту.
      </p>

      <Button
          label="Скачать PNG"
          icon="pi pi-download"
          class="!bg-primary-600 !border-none !w-full"
          @click="downloadQr"
      />
    </div>
  </Dialog>
</template>