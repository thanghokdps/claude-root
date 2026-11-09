import { Module } from '@nestjs/common';
import { APP_FILTER } from '@nestjs/core';
import { AppExceptionFilter } from './common/app-exception.filter';
import { DbModule } from './db/db.module';
import { ChannelsModule } from './modules/channels/channels.module';

@Module({
  imports: [DbModule, ChannelsModule],
  providers: [{ provide: APP_FILTER, useClass: AppExceptionFilter }],
})
export class AppModule {}
