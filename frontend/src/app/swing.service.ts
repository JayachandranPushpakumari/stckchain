import { Injectable } from '@angular/core';
import { environment } from '../environments/environment';
import { HttpClient } from '@angular/common/http';
import { Observable, of, tap } from 'rxjs';

export interface SwingStock {
  symbol: string;
  sector?: string | null;
  latest_close: number | null;
  total_score: number;
  category_scores: Record<string, SwingCriterionScore>;
}

export interface SwingCriterionScore {
  actual_value: number | null;
  threshold: number | null;
  operator: string;
  score: number;
}

export interface SwingResponse {
  symbols: SwingStock[];
}

export interface BreakoutStock {
  symbol: string;
  close: number;
  rsi: number;
  volume_ratio: number;
  ma20: number;
  ma50: number;
  high_20: number;
  adx: number;
  signal: string;
}

export interface StockHistoryPoint {
  date: string;
  close: number;
}

export interface StockHistoryResponse {
  symbol: string;
  frequency: string;
  prices: StockHistoryPoint[];
}

export interface BacktestResult {
  symbol: string;
  total_trades: number;
  win_rate: number;
  avg_return: number;
  profit_factor: number;
  max_drawdown: number;
  cagr: number;
}

export interface Trade {
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  return: number;
  exit_reason: string;
}

export interface OpportunityBacktestMetrics {
  total_trades: number;
  win_rate: number;
  avg_return: number;
  profit_factor: number | null;
  max_drawdown: number;
  target_1_rate: number;
  target_2_rate: number;
  stop_loss_rate: number;
  timeout_rate: number;
  avg_mfe: number;
  avg_mae: number;
}

export interface OpportunityBacktestResult {
  id?: number;
  run_id?: number;
  strategy: string;
  start_date: string;
  end_date: string;
  generated_at: string;
  stage_counts: Record<string, number>;
  metrics: OpportunityBacktestMetrics;
  trades: unknown[];
}

export interface SingleSymbolBacktestResult {
  symbol?: string;
  total_trades?: number;
  win_rate?: number;
  avg_return?: number;
  profit_factor?: number;
  max_drawdown?: number;
  cagr?: number;
  total_data_points?: number;
  trades_list?: Trade[];
  error?: string;
  data_points?: number;
}

interface BreakoutCachePayload {
  timestamp: number;
  data: BreakoutStock[];
}

interface SwingCachePayload {
  timestamp: number;
  data: SwingResponse;
}

interface HistoryCachePayload {
  timestamp: number;
  data: StockHistoryResponse;
}

@Injectable({ providedIn: 'root' })
export class SwingService {
  private readonly swingEndpoint = `${environment.apiUrl}/screen/swing`;
  private readonly breakoutEndpoint = `${environment.apiUrl}/screen/breakout`;
  private readonly stockHistoryEndpoint = `${environment.apiUrl}/stocks`;
  private readonly backtestResultsEndpoint = `${environment.apiUrl}/backtest/results`;
  private readonly backtestTopStrategiesEndpoint = `${environment.apiUrl}/backtest/top-strategies`;
  private readonly runBacktestEndpoint = `${environment.apiUrl}/backtest/breakout`;
  private readonly opportunityBacktestEndpoint = `${environment.apiUrl}/backtest/opportunities`;
  private readonly swingCacheKey = 'stockchain_swing_cache_v2';
  private readonly breakoutCacheKey = 'stockchain_breakout_cache_v2';
  private readonly historyCachePrefix = 'stockchain_history_cache_v1_';
  private readonly swingCacheTtlMs = 24 * 60 * 60 * 1000;
  private readonly breakoutCacheTtlMs = 24 * 60 * 60 * 1000;
  private readonly historyCacheTtlMs = 12 * 60 * 60 * 1000;
  private readonly defaultHistoryLimit = 100;

  constructor(private readonly http: HttpClient) {}

  getSwingScreen(forceRefresh = false): Observable<SwingResponse> {
    const cachedData = forceRefresh ? null : this.getCachedSwingData();
    if (cachedData) {
      return of(cachedData);
    }

    return this.http.get<SwingResponse>(this.swingEndpoint).pipe(
      tap((data) => this.setCachedSwingData(data ?? { symbols: [] })),
    );
  }

  getBreakoutScreen(forceRefresh = false): Observable<BreakoutStock[]> {
    const cachedData = forceRefresh ? null : this.getCachedBreakoutData();
    if (cachedData) {
      return of(cachedData);
    }

    return this.http.get<BreakoutStock[]>(this.breakoutEndpoint).pipe(
      tap((data) => this.setCachedBreakoutData(data ?? [])),
    );
  }

  getStockHistory(symbol: string, forceRefresh = false): Observable<StockHistoryResponse> {
    const cacheKey = this.getHistoryCacheKey(symbol);
    const cachedData = forceRefresh ? null : this.getCachedHistoryData(cacheKey);
    if (cachedData) {
      return of(cachedData);
    }

    const url = `${this.stockHistoryEndpoint}/${encodeURIComponent(symbol)}/history?limit=${this.defaultHistoryLimit}`;
    return this.http.get<StockHistoryResponse>(url).pipe(
      tap((data) => this.setCachedHistoryData(cacheKey, data ?? { symbol, frequency: '1D', prices: [] })),
    );
  }

  private getCachedSwingData(): SwingResponse | null {
    const raw = localStorage.getItem(this.swingCacheKey);
    if (!raw) {
      return null;
    }

    try {
      const payload = JSON.parse(raw) as SwingCachePayload;
      const isExpired = Date.now() - payload.timestamp > this.swingCacheTtlMs;
      const isMissingSectorData = (payload.data?.symbols ?? []).some((stock) => !('sector' in stock));
      if (isExpired || isMissingSectorData) {
        localStorage.removeItem(this.swingCacheKey);
        return null;
      }

      return payload.data;
    } catch {
      localStorage.removeItem(this.swingCacheKey);
      return null;
    }
  }

  private setCachedSwingData(data: SwingResponse): void {
    try {
      const payload: SwingCachePayload = {
        timestamp: Date.now(),
        data,
      };
      localStorage.setItem(this.swingCacheKey, JSON.stringify(payload));
    } catch {
      localStorage.removeItem(this.swingCacheKey);
    }
  }

  private getCachedBreakoutData(): BreakoutStock[] | null {
    const raw = localStorage.getItem(this.breakoutCacheKey);
    if (!raw) {
      return null;
    }

    try {
      const payload = JSON.parse(raw) as BreakoutCachePayload;
      const isExpired = Date.now() - payload.timestamp > this.breakoutCacheTtlMs;
      if (isExpired) {
        localStorage.removeItem(this.breakoutCacheKey);
        return null;
      }

      return Array.isArray(payload.data) ? payload.data : null;
    } catch {
      localStorage.removeItem(this.breakoutCacheKey);
      return null;
    }
  }

  private setCachedBreakoutData(data: BreakoutStock[]): void {
    const payload: BreakoutCachePayload = {
      timestamp: Date.now(),
      data,
    };
    localStorage.setItem(this.breakoutCacheKey, JSON.stringify(payload));
  }

  private getHistoryCacheKey(symbol: string): string {
    return `${this.historyCachePrefix}${symbol.toUpperCase()}`;
  }

  private getCachedHistoryData(cacheKey: string): StockHistoryResponse | null {
    const raw = localStorage.getItem(cacheKey);
    if (!raw) {
      return null;
    }

    try {
      const payload = JSON.parse(raw) as HistoryCachePayload;
      const isExpired = Date.now() - payload.timestamp > this.historyCacheTtlMs;
      if (isExpired) {
        localStorage.removeItem(cacheKey);
        return null;
      }

      return payload.data;
    } catch {
      localStorage.removeItem(cacheKey);
      return null;
    }
  }

  private setCachedHistoryData(cacheKey: string, data: StockHistoryResponse): void {
    const payload: HistoryCachePayload = {
      timestamp: Date.now(),
      data,
    };
    localStorage.setItem(cacheKey, JSON.stringify(payload));
  }

  getBacktestResults(): Observable<BacktestResult[]> {
    return this.http.get<BacktestResult[]>(this.backtestResultsEndpoint);
  }

  getTopStrategies(): Observable<BacktestResult[]> {
    return this.http.get<BacktestResult[]>(this.backtestTopStrategiesEndpoint);
  }

  runBacktest(): Observable<{ status: string; data: BacktestResult[] }> {
    return this.http.get<{ status: string; data: BacktestResult[] }>(this.runBacktestEndpoint);
  }

  backtestSymbol(symbol: string): Observable<SingleSymbolBacktestResult> {
    const url = `${environment.apiUrl}/backtest/symbol/${encodeURIComponent(symbol.toUpperCase())}`;
    return this.http.get<SingleSymbolBacktestResult>(url);
  }

  getLatestOpportunityBacktest(): Observable<OpportunityBacktestResult> {
    return this.http.get<OpportunityBacktestResult>(`${this.opportunityBacktestEndpoint}/latest`);
  }

  runOpportunityBacktest(): Observable<OpportunityBacktestResult> {
    return this.http.post<OpportunityBacktestResult>(`${this.opportunityBacktestEndpoint}/run`, {});
  }
}
