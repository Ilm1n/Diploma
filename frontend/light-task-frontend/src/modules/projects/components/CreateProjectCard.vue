<template>
  <button
      class="group h-32 flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed transition-all duration-300 cursor-pointer active:scale-[0.98]
    border-slate-400 bg-slate-50 hover:border-primary-500 hover:bg-primary-50
    dark:border-slate-600 dark:bg-transparent  dark:hover:bg-slate-800 dark:hover:border-primary-500"
  >
    <div
        class="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-sm group-hover:scale-110 group-hover:shadow-md
      bg-white text-slate-400 border border-slate-300 dark:border-slate-600 group-hover:text-primary-600
      dark:bg-slate-800 dark:text-slate-400 dark:group-hover:bg-slate-700 dark:group-hover:text-primary-400"
    >
      <i class="pi pi-plus text-xl font-bold"></i>
    </div>

    <span
        class="text-sm font-bold transition-colors
      text-slate-500 group-hover:text-primary-700
      dark:text-slate-400 dark:group-hover:text-primary-400"
    >
      Создать проект
    </span>
  </button>
</template>