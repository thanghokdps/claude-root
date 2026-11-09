import { Inject, Injectable } from '@nestjs/common';
import { AppError } from '../../common/app-error';
import type { SessionUser } from '../../common/session.guard';
import { DB, type Db } from '../../db/db.module';
import * as repo from './channels.repository';
import type { ChannelDto } from './channels.schema';

@Injectable()
export class ChannelsService {
  constructor(@Inject(DB) private readonly db: Db) {}

  async getChannelForUser(user: SessionUser, channelId: number): Promise<ChannelDto> {
    const channel = await repo.findChannel(this.db, user.workspaceId, channelId);
    if (!channel) throw new AppError('channel_not_found', 404);
    return { id: channel.id, name: channel.name, createdAt: channel.createdAt.toISOString() };
  }
}
