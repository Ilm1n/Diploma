export function getPlural(
  number: number,
  titles: readonly [string, string, string],
): string {
  // Пример - [задача, задачи, задач]
  const mod100 = number % 100;

  if (mod100 > 4 && mod100 < 20) {
    return titles[2];
  }

  const mod10 = number % 10;

  if (mod10 === 1) {
    return titles[0];
  }

  if (mod10 >= 2 && mod10 <= 4) {
    return titles[1];
  }

  return titles[2];
}
