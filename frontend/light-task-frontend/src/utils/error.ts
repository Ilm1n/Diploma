import { ApiError } from '@/api/client';
import { RU_ERROR_MESSAGES } from '@/i18n/error-messages';

type ErrorParams = Record<string, unknown>;

type ApiErrorBody = {
  error?: {
    code?: string;
    params?: ErrorParams;
  };
  detail?: unknown;
  message?: string;
};

const ERROR_CODE_PATTERN = /^[A-Z0-9_]+$/;

function formatTemplate(
  template: string,
  params: ErrorParams | undefined,
): string {
  if (!params) return template;

  return template.replace(/\{(\w+)\}/g, (_, key: string) => {
    const value = params[key];
    if (Array.isArray(value)) return value.join(', ');
    if (value === null || value === undefined) return `{${key}}`;
    return String(value);
  });
}

function getMessageByCode(code: string, params?: ErrorParams): string {
  const template = RU_ERROR_MESSAGES[code];
  if (!template) {
    return RU_ERROR_MESSAGES.UNKNOWN_ERROR;
  }
  return formatTemplate(template, params);
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body as ApiErrorBody;

    const code = body?.error?.code;
    if (typeof code === 'string') {
      return getMessageByCode(code, body?.error?.params);
    }

    if (body?.detail && Array.isArray(body.detail)) {
      const firstError = body.detail[0];
      return `${firstError.msg}`;
    }

    if (body?.detail && typeof body.detail === 'string') {
      if (ERROR_CODE_PATTERN.test(body.detail)) {
        return getMessageByCode(body.detail);
      }
      return body.detail;
    }

    if (body?.message) {
      return body.message;
    }

    if (typeof body === 'string') {
      return body;
    }

    return error.message || RU_ERROR_MESSAGES.UNKNOWN_ERROR;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return RU_ERROR_MESSAGES.UNKNOWN_ERROR;
}
