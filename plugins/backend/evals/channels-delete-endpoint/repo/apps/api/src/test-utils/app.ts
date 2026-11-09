import { FastifyAdapter, type NestFastifyApplication } from '@nestjs/platform-fastify';
import { Test } from '@nestjs/testing';
import { AppModule } from '../app.module';
import { SessionGuard } from '../common/session.guard';
import { createDb, DB, type Db } from '../db/db.module';
import { channels } from '../db/schema';

export type TestApp = NestFastifyApplication & { db: Db };

// Real Postgres (TEST_DATABASE_URL, migrated with drizzle/), only the session guard replaced.
export async function createTestApp(): Promise<TestApp> {
  const db = createDb(process.env.TEST_DATABASE_URL!);
  const moduleRef = await Test.createTestingModule({ imports: [AppModule] })
    .overrideProvider(DB)
    .useValue(db)
    .overrideGuard(SessionGuard)
    .useValue({
      canActivate: (ctx: any) => {
        const req = ctx.switchToHttp().getRequest();
        const id = Number(req.headers['x-test-user']);
        if (!id) return false;
        req.user = { id, workspaceId: id };
        return true;
      },
    })
    .compile();
  const app = moduleRef.createNestApplication<NestFastifyApplication>(new FastifyAdapter());
  await app.init();
  await app.getHttpAdapter().getInstance().ready();
  return Object.assign(app, { db });
}

export function signInAs(userId: number) {
  return { 'x-test-user': String(userId) };
}

export async function seedChannel(db: Db, values: { workspaceId: number; createdBy: number; name?: string }) {
  const [row] = await db
    .insert(channels)
    .values({ ...values, name: values.name ?? `general-${Date.now()}` })
    .returning();
  return row;
}
