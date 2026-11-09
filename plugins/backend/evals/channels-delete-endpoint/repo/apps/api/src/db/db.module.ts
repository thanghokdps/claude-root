import { Global, Module } from '@nestjs/common';
import { drizzle } from 'drizzle-orm/node-postgres';
import { Pool } from 'pg';
import * as schema from './schema';

export const DB = Symbol('DB');
export type Db = ReturnType<typeof createDb>;

export function createDb(connectionString: string) {
  const pool = new Pool({ connectionString });
  return drizzle({ client: pool, schema });
}

// The one pool per process: every module injects DB from here.
@Global()
@Module({
  providers: [{ provide: DB, useFactory: () => createDb(process.env.DATABASE_URL!) }],
  exports: [DB],
})
export class DbModule {}
