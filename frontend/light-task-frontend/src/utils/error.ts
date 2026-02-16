import { ApiError } from '@/api/client';

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body;

    if (body?.detail && Array.isArray(body.detail)) {
      const firstError = body.detail[0];
      return `${firstError.msg}`;
    }

    if (body?.detail && typeof body.detail === 'string') {
      return body.detail;
    }

    if (body?.message) {
      return body.message;
    }

    if (typeof body === 'string') {
      return body;
    }

    return error.message || 'Произошла ошибка API';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Неизвестная ошибка';
}