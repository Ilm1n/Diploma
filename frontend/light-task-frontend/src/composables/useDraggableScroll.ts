import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue';

export function useDraggableScroll(containerRef: Ref<HTMLElement | null>) {
  const isDragging = ref(false);
  let startX = 0;
  let scrollLeft = 0;

  const onMouseDown = (e: MouseEvent) => {
    const el = containerRef.value;
    if (!el) return;

    const target = e.target as HTMLElement;
    if (
      target.closest('button') ||
      target.closest('input') ||
      target.closest('textarea') ||
      target.closest('.column-drag-handle') ||
      target.closest('.task-card')
    ) {
      return;
    }

    isDragging.value = true;
    startX = e.pageX - el.offsetLeft;
    scrollLeft = el.scrollLeft;

    document.body.style.cursor = 'grabbing';
    document.body.style.userSelect = 'none';

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const onMouseMove = (e: MouseEvent) => {
    if (!isDragging.value) return;

    const el = containerRef.value;
    if (!el) return;

    e.preventDefault();

    const x = e.pageX - el.offsetLeft;
    const walk = (x - startX) * 1.5; // Скорость скролла
    el.scrollLeft = scrollLeft - walk;
  };

  const onMouseUp = () => {
    isDragging.value = false;

    document.body.style.cursor = '';
    document.body.style.removeProperty('user-select');

    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  };

  onMounted(() => {
    const el = containerRef.value;
    if (el) {
      el.addEventListener('mousedown', onMouseDown);
    }
  });

  onBeforeUnmount(() => {
    const el = containerRef.value;
    if (el) {
      el.removeEventListener('mousedown', onMouseDown);
    }
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  });

  return {
    isDragging
  };
}