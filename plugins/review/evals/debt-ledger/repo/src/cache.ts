// shortcut: in-memory map, fine for one process; move to Redis when we run more than one instance
const seen = new Map<string, number>();

export function markSeen(orderId: string): boolean {
  if (seen.has(orderId)) return false;
  seen.set(orderId, Date.now());
  return true;
}
