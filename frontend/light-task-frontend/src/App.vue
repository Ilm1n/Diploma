<script setup lang="ts">
import Toast from 'primevue/toast';
import ConfirmDialog from "primevue/confirmdialog";
</script>

<template>
  <ConfirmDialog />
  <Toast />
  <router-view />
</template>