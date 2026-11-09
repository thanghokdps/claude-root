import { and, eq } from 'drizzle-orm';
import type { Db } from '../../db/db.module';
import { channels } from '../../db/schema';

export async function findChannel(db: Db, workspaceId: number, channelId: number) {
  const rows = await db
    .select({ id: channels.id, name: channels.name, createdBy: channels.createdBy, createdAt: channels.createdAt })
    .from(channels)
    .where(and(eq(channels.id, channelId), eq(channels.workspaceId, workspaceId)))
    .limit(1);
  return rows[0] ?? null;
}

export async function listChannels(db: Db, workspaceId: number, limit = 50) {
  return db
    .select({ id: channels.id, name: channels.name, createdBy: channels.createdBy, createdAt: channels.createdAt })
    .from(channels)
    .where(eq(channels.workspaceId, workspaceId))
    .orderBy(channels.createdAt, channels.id)
    .limit(Math.min(limit, 100));
}
