/**
 * Server-side provider selection. Only the mock is enabled.
 * MODELFLOW_PROVIDER=bedrock selects the stub, which throws "not enabled".
 */
import { BedrockChatProvider, BedrockPlannerProvider } from "./bedrockProvider";
import { MockChatProvider } from "./mockChat";
import { MockPlannerProvider } from "./mockPlanner";
import type { ChatProvider, PlannerProvider } from "./types";

export function getPlannerProvider(env: Record<string, string | undefined> = process.env): PlannerProvider {
  return env.MODELFLOW_PROVIDER === "bedrock" ? new BedrockPlannerProvider() : new MockPlannerProvider();
}

export function getChatProvider(env: Record<string, string | undefined> = process.env): ChatProvider {
  return env.MODELFLOW_PROVIDER === "bedrock" ? new BedrockChatProvider() : new MockChatProvider();
}
