export type MarketRegime = 'BULL' | 'NEUTRAL' | 'WEAK' | 'BEAR' | 'UNKNOWN';

export interface OpportunityStageCounts {
  all_stocks: number;
  data_quality: number;
  liquidity: number;
  fundamentals: number;
  breakout: number;
  market_regime: number;
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
