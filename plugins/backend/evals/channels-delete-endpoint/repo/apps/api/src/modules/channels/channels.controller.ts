import { Controller, Get, Param, UseGuards } from '@nestjs/common';
import { CurrentUser } from '../../common/current-user.decorator';
import { SessionGuard, type SessionUser } from '../../common/session.guard';
import { ZodValidationPipe } from '../../common/zod-validation.pipe';
import { channelIdSchema, type ChannelDto } from './channels.schema';
import { ChannelsService } from './channels.service';

@Controller('channels')
@UseGuards(SessionGuard)
export class ChannelsController {
  constructor(private readonly channels: ChannelsService) {}

  @Get(':id')
  getChannel(
    @CurrentUser() user: SessionUser,
    @Param('id', new ZodValidationPipe(channelIdSchema)) id: number,
  ): Promise<ChannelDto> {
    return this.channels.getChannelForUser(user, id);
  }
}
