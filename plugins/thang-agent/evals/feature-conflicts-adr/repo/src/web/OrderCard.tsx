import { useRenderTool } from "@copilotkit/react-core/v2";

export function useOrderCard() {
  useRenderTool({ name: "getOrder", render: ({ result }) => (result ? <div className="order-card">{result.code} — {result.status}</div> : <div>…</div>) });
}
