export type WorkloadMode = "controlled" | "mixed";

export interface ExperimentParams {
  num_requests: number;
  num_concurrent: number;
  fixed_draft_length: number;
  max_adaptive_draft_length: number;
  max_draft_length: number;
  base_acceptance: number;
  acceptance_decay: number;
  draft_cost_per_token: number;
  target_cost_per_token: number;
  verify_cost_base: number;
  verify_efficiency_at_concurrency: number;
  saturation_concurrency: number;
  memory_pressure_factor: number;
  output_tokens_per_request: number;
  prompt_length: number;
  verification_budget: number;
  estimation_noise: number;
  speculation_overhead: number;
  random_seed: number;
  workload_mode: WorkloadMode;
  sequence_length_cost_scale: number;
}

export interface BatchAggregates {
  seeds: number[];
  num_seeds: number;
  aggregates: Record<
    string,
    Record<
      string,
      {
        mean: number;
        std: number;
        min: number;
        max: number;
      }
    >
  >;
  disclaimer: string;
}

export interface ReplayStep {
  step: number;
  sequence_length: number;
  draft_length: number;
  draft_accepted: number;
  draft_rejected: number;
  bonus_tokens: number;
  tokens_produced: number;
  execution_cost: number;
  remaining_tokens: number;
  cumulative_cost: number;
  sim_time: number;
}

export interface ReplayResponse {
  policy: string;
  request: {
    prompt_length: number;
    output_tokens: number;
    base_acceptance: number;
    acceptance_decay: number;
  };
  steps: ReplayStep[];
  completed: boolean;
  disclaimer: string;
}

export interface PresetInfo {
  id: string;
  name: string;
  description: string;
  overrides: Partial<ExperimentParams>;
}

export interface HypothesisEvaluation {
  supported: boolean | null;
  message: string;
  checks: { id: string; passed: boolean; detail: string }[];
  details?: string[];
}

export interface PolicyResult {
  policy: string;
  throughput_tokens_per_sec: number;
  mean_latency: number;
  p95_latency: number;
  total_execution_cost: number;
  avg_accepted_per_verification: number;
  draft_tokens_rejected: number;
  verification_operations: number;
  speculation_efficiency: number;
  total_output_tokens: number;
  draft_tokens_accepted: number;
  draft_tokens_proposed: number;
  completion_time: number;
}

export interface ExperimentResponse {
  results: Record<string, PolicyResult>;
  insights: string[];
  charts: {
    draft_length_vs_useful: { draft_length: number; expected_accepted: number; expected_with_bonus: number }[];
    wasted_verification: {
      fixed: { accepted: number; rejected: number };
      adaptive: { accepted: number; rejected: number };
    };
  };
  meta: {
    random_seed: number;
    workload_mode: string;
    num_requests: number;
    disclaimer: string;
  };
}

export interface ConcurrencySweepPoint {
  concurrency: number;
  policy: string;
  throughput_tokens_per_sec: number;
  mean_latency: number;
  p95_latency: number;
}
