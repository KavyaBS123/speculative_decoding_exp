export const POLICY_LABELS: Record<string, string> = {
  standard: "Standard AR",
  fixed_speculative: "Fixed speculative",
  adaptive: "Adaptive",
};

export const POLICY_COLORS: Record<string, string> = {
  standard: "#94a3b8",
  fixed_speculative: "#60a5fa",
  adaptive: "#3dd6c3",
};

export function policyLabel(key: string): string {
  return POLICY_LABELS[key] ?? key;
}
