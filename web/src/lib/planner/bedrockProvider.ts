/**
 * Placeholder for the real Bedrock planner/chat (M7.2 / M7.3).
 *
 * Intentionally NOT implemented: no SDK import, no credentials, no network.
 * Enabling it requires the user's approval of model, pricing, per-request
 * token limits, invocation caps and a dev/test budget (handoff section 14).
 */
import {
  ProviderNotEnabledError,
  type ChatProvider,
  type ChatRequest,
  type ChatResponse,
  type PlanRequest,
  type PlanResponse,
  type PlannerProvider,
} from "./types";

export const BEDROCK_NOT_ENABLED = "Bedrock provider not enabled — requires user-approved budget";

export class BedrockPlannerProvider implements PlannerProvider {
  readonly kind = "bedrock" as const;
  async plan(req: PlanRequest): Promise<PlanResponse> {
    void req;
    throw new ProviderNotEnabledError(BEDROCK_NOT_ENABLED);
  }
}

export class BedrockChatProvider implements ChatProvider {
  readonly kind = "bedrock" as const;
  async respond(req: ChatRequest): Promise<ChatResponse> {
    void req;
    throw new ProviderNotEnabledError(BEDROCK_NOT_ENABLED);
  }
}
