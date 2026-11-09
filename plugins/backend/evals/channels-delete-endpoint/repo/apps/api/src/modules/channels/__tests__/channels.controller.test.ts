import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { createTestApp, seedChannel, signInAs, type TestApp } from '../../../test-utils/app';

describe('GET /channels/:id', () => {
  let app: TestApp;
  beforeAll(async () => {
    app = await createTestApp();
  });
  afterAll(() => app.close());

  it('returns the caller workspace channel', async () => {
    const channel = await seedChannel(app.db, { workspaceId: 1, createdBy: 1 });
    const res = await app.inject({ method: 'GET', url: `/channels/${channel.id}`, headers: signInAs(1) });
    expect(res.statusCode).toBe(200);
    expect(res.json()).toMatchObject({ id: channel.id, name: channel.name });
  });

  it('answers 404 channel_not_found for another workspace channel', async () => {
    const channel = await seedChannel(app.db, { workspaceId: 2, createdBy: 2 });
    const res = await app.inject({ method: 'GET', url: `/channels/${channel.id}`, headers: signInAs(1) });
    expect(res.statusCode).toBe(404);
    expect(res.json()).toEqual({ error: 'channel_not_found' });
  });

  it('answers 401 without a session', async () => {
    const res = await app.inject({ method: 'GET', url: '/channels/1' });
    expect(res.statusCode).toBe(401);
  });
});
