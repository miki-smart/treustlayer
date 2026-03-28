/** In-memory blocks from webhooks / risk updates (demo; use Redis in production). */

const blockedByUser = new Map<string, { reason: string; at: number }>();

export function isUserBlocked(userId: string): { blocked: boolean; reason?: string } {
  const b = blockedByUser.get(userId);
  if (!b) return { blocked: false };
  return { blocked: true, reason: b.reason };
}

export function blockUser(userId: string, reason: string): void {
  blockedByUser.set(userId, { reason, at: Date.now() });
}

export function unblockUser(userId: string): void {
  blockedByUser.delete(userId);
}

export function resetBlocks(): void {
  blockedByUser.clear();
}
