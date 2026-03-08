import { RU_SUCCESS_MESSAGES } from '@/i18n/success-messages';

type SuccessParams = Record<string, unknown>;

type ApiSuccessPayload = {
  code?: string;
  params?: SuccessParams | null;
};

function formatTemplate(template: string, params?: SuccessParams | null): string {
  if (!params) return template;

  return template.replace(/\{(\w+)\}/g, (_, key: string) => {
    const value = params[key];
    if (Array.isArray(value)) return value.join(', ');
    if (value === null || value === undefined) return `{${key}}`;
    return String(value);
  });
}

export function getSuccessMessage(
  success: ApiSuccessPayload | null | undefined,
  fallback = 'Операция выполнена успешно',
): string {
  if (!success?.code) return fallback;

  const template = RU_SUCCESS_MESSAGES[success.code];
  if (!template) return fallback;

  return formatTemplate(template, success.params);
}
