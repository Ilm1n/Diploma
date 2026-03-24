const mutationStack: string[] = [];

export function currentClientMutationId(): string | null {
  return mutationStack.length > 0 ? (mutationStack[mutationStack.length - 1] ?? null) : null;
}

export async function withClientMutationId<T>(
  callback: (mutationId: string) => Promise<T>,
): Promise<T> {
  const mutationId = crypto.randomUUID();
  mutationStack.push(mutationId);
  try {
    return await callback(mutationId);
  } finally {
    mutationStack.pop();
  }
}
