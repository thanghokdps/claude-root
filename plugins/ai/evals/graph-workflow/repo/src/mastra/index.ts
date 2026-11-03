import { Mastra } from "@mastra/core";
import { supportAgent } from "./agents/support-agent";

export const mastra = new Mastra({
  agents: { support: supportAgent },
});
