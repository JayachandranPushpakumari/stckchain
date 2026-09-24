export type MarketRegime = 'BULL' | 'NEUTRAL' | 'WEAK' | 'BEAR' | 'UNKNOWN';

export interface OpportunityStageCounts {
  all_stocks: number;
  data_quality: number;
  liquidity: number;
  fundamentals: number;
  breakout: number;
  market_regime: number;
  chart_pattern?: number;
  risk_reward: number;
  high_confidence: number;
}

export interface StockChainOpportunity {
  symbol: string;
  setup_type: string;
  status: string;
  rank: number;
  score: number;
  current_price: number;
  entry_low: number;
  entry_high: number;
  target_1: number;
  target_2: number;
  stop_loss: number;
  risk_reward: number;
  fundamental_score: number;
  technical_score: number;
  momentum_score: number;
  liquidity_score: number;
  regime_score: number;
  risk_reward_score: number;
  market_regime: MarketRegime;
  reasons: string[];
}

export interface MarketRegimeDetail {
  regime: MarketRegime;
  score: number;
  reason: string;
  breadth?: number | null;
  nifty_close?: number;
  nifty_ma50?: number;
  nifty_ma200?: number;
}

export interface OpportunityRun {
  run_id?: number;
  generated_at?: string;
  setup_type?: string;
  market_regime: MarketRegime | MarketRegimeDetail;
  stage_counts?: OpportunityStageCounts;
  minimum_score?: number;
  message: string | null;
  opportunities: StockChainOpportunity[];
}

export interface BreakoutDiagnostic {
  symbol: string;
  fundamental_score: number | null;
  data_quality_pass: boolean;
  liquidity_pass: boolean;
  fundamental_pass: boolean;
  patterns: string[];
  pattern_reasons: string[];
  pattern_result: string;
  risk_reward_result: string | null;
  opportunity: StockChainOpportunity | null;
  rejection_reason: string | null;
}

export interface BreakoutDiagnosticsRun {
  generated_at: string;
  market_regime: MarketRegime | MarketRegimeDetail;
  candidate_count: number;
  published_count: number;
  diagnostics: BreakoutDiagnostic[];
}
