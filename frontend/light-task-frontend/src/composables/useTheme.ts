import {ref, watchEffect} from 'vue';

const isDark = ref(localStorage.getItem('theme') === 'dark');

export function useTheme() {
  const toggleTheme = () => {
    isDark.value = !isDark.value;
  };

  watchEffect(() => {
    const html = document.documentElement;
    if (isDark.value) {
      html.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      html.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  });

  return {
    isDark,
    toggleTheme
  };
}