import { z } from 'zod';

export const channelIdSchema = z.coerce.number().int().positive();

export const channelDtoSchema = z.object({
  id: z.number(),
  name: z.string(),
  createdAt: z.string(),
});
export type ChannelDto = z.infer<typeof channelDtoSchema>;
