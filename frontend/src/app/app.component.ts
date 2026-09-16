import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BacktestResult, BreakoutStock, SingleSymbolBacktestResult, StockHistoryPoint, SwingCriterionScore, SwingService, SwingStock } from './swing.service';
import { SectorHeatmapComponent } from './components/sector-heatmap/sector-heatmap.component';
import { HeatmapService, SectorHeatmapItem, SectorRotationRankItem } from './services/heatmap.service';
import { SeasonalStocksComponent } from './components/seasonal-stocks/seasonal-stocks.component';
import { AuthService } from './auth.service';

type SortOption = 'scoreDesc' | 'scoreAsc' | 'symbolAsc' | 'symbolDesc' | 'promoterHolding' | 'breakoutOverlap' | 'sectorLeader';
type ScreenerTab = 'swing' | 'breakout' | 'heatmap' | 'seasonality' | 'backtest';
type ScoreFilterOption = 'all' | '60' | '70' | '80' | '90';
type SectorPeriodOption = '1d' | '1w' | '1m' | '3m' | '6m' | '1y';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule, SectorHeatmapComponent, SeasonalStocksComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent implements OnInit {
  private readonly defaultVisibleStocksCount = 50;
  private readonly breakoutSymbols = new Set<string>();
  private readonly sectorLeaderSymbols = new Set<string>();
  chartOnlyMode = false;
  loading = true;
  error = '';
  stocks: SwingStock[] = [];
  visibleStocks: SwingStock[] = [];
  displayedStocks: SwingStock[] = [];
  showAllStocks = false;
  hasMoreSwingStocks = false;
  avgScore = 0;
  breakoutLoading = true;
  breakoutError = '';
  breakoutStocks: BreakoutStock[] = [];
  sectorHeatmapLoading = true;
  sectorHeatmapError = '';
  sectorHeatmapSectors: SectorHeatmapItem[] = [];
  sectorRotationLoading = true;
  sectorRotationError = '';
  sectorRotationRanks: SectorRotationRankItem[] = [];
  sectorPeriodOptions: { value: SectorPeriodOption; label: string }[] = [
    { value: '1d', label: '1 Day' },
    { value: '1w', label: '1 Week' },
    { value: '1m', label: '1 Month' },
    { value: '3m', label: '3 Months' },
    { value: '6m', label: '6 Months' },
    { value: '1y', label: '1 Year' },
  ];
  selectedSectorPeriod: SectorPeriodOption = '3m';
  searchQuery = '';
  scoreFilterOption: ScoreFilterOption = 'all';
  sortOption: SortOption = 'scoreDesc';
  activeTab: ScreenerTab = 'swing';
  selectedSwingSymbol = '';
  swingChartLoading = false;
  swingChartError = '';
  swingChartPoints: StockHistoryPoint[] = [];
  hasSwingChartData = false;
  swingChartStartDate = '-';
  swingChartEndDate = '-';
  swingChartLatestClose = 0;
  swingChartLow = 0;
  swingChartHigh = 0;
  swingChartPolylinePoints = '';
  backtestLoading = false;
  backtestError = '';
  backtestResults: BacktestResult[] = [];
  topStrategies: BacktestResult[] = [];
  backtestRunning = false;
  symbolBacktestInput = '';
  symbolBacktestLoading = false;
  symbolBacktestError = '';
  symbolBacktestResult: SingleSymbolBacktestResult | null = null;
  showAllTrades = false;
  loginUsername = '';
  loginPassword = '';
  loginLoading = false;
  loginError = '';

  constructor(
    private readonly swingService: SwingService,
    private readonly heatmapService: HeatmapService,
    private readonly cdr: ChangeDetectorRef,
    protected readonly auth: AuthService,
  ) {}

  ngOnInit(): void {
    if (this.auth.isAuthenticated()) {
      this.initializeDashboard();
    }
  }

  onLogin(): void {
    const username = this.loginUsername.trim();
    if (!username || !this.loginPassword) {
      this.loginError = 'Enter your username and password.';
      return;
    }

    this.loginLoading = true;
    this.loginError = '';

    this.auth.login(username, this.loginPassword).subscribe({
      next: () => {
        this.loginLoading = false;
        this.loginPassword = '';
        this.initializeDashboard();
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.loginError =
          err?.status === 401
            ? 'Invalid username or password.'
            : 'Unable to reach the backend. Please try again.';
        this.loginLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  onLogout(): void {
    this.auth.logout();
  }

  private initializeDashboard(): void {
    const params = new URLSearchParams(globalThis.location.search);
    this.chartOnlyMode = params.get('chartOnly') === '1';
    const initialSymbol = params.get('symbol')?.trim();

    if (this.chartOnlyMode) {
      if (initialSymbol) {
        this.activeTab = 'swing';
        this.openSwingChart(initialSymbol.toUpperCase());
      } else {
        this.swingChartError = 'No symbol provided for chart view.';
        this.cdr.markForCheck();
      }
      return;
    }

    this.refreshData();

    if (initialSymbol) {
      this.activeTab = 'swing';
      this.openSwingChart(initialSymbol.toUpperCase());
    }
  }

  loadBreakoutData(forceRefresh = false): void {
    this.breakoutLoading = true;
    this.breakoutError = '';

    this.swingService.getBreakoutScreen(forceRefresh).subscribe({
      next: (response) => {
        this.breakoutStocks = response ?? [];
        this.breakoutSymbols.clear();
        for (const stock of this.breakoutStocks) {
          if (stock.symbol) {
            this.breakoutSymbols.add(stock.symbol.toUpperCase());
          }
        }
        this.breakoutLoading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.breakoutSymbols.clear();
        this.breakoutError = 'Unable to load breakout screener data. Make sure backend is running on :8000.';
        this.breakoutLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  openSwingChartInNewTab(symbol: string): void {
    const url = `${globalThis.location.origin}${globalThis.location.pathname}?chartOnly=1&symbol=${encodeURIComponent(symbol)}`;
    globalThis.open(url, '_blank', 'noopener,noreferrer');
  }

  trackBySymbol(_: number, stock: SwingStock): string {
    return stock.symbol;
  }

  openSwingChart(symbol: string, forceRefresh = false): void {
    this.selectedSwingSymbol = symbol;
    this.swingChartLoading = true;
    this.swingChartError = '';
    this.setSwingChartPoints([]);

    this.swingService.getStockHistory(symbol, forceRefresh).subscribe({
      next: (response) => {
        this.setSwingChartPoints(response.prices ?? []);
        if (!this.swingChartPoints.length) {
          this.swingChartError = 'No daily price history found for this stock.';
        }
        this.swingChartLoading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.swingChartError = 'Unable to load chart data from backend.';
        this.swingChartLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  closeSwingChart(): void {
    this.selectedSwingSymbol = '';
    this.swingChartLoading = false;
    this.swingChartError = '';
    this.setSwingChartPoints([]);
  }

  trackByBreakoutSymbol(_: number, stock: BreakoutStock): string {
    return stock.symbol;
  }

  shouldPulseSwingCard(stock: SwingStock): boolean {
    return this.hasBreakoutOverlap(stock) || this.hasIncreasedPromoterHolding(stock) || this.isSectorLeader(stock);
  }

  hasBreakoutOverlap(stock: SwingStock): boolean {
    return this.breakoutSymbols.has(stock.symbol.toUpperCase());
  }

  hasIncreasedPromoterHolding(stock: SwingStock): boolean {
    const promoterHolding = stock.category_scores?.['pledged_promoter_holding']?.actual_value;
    return promoterHolding !== null && promoterHolding !== undefined && promoterHolding < 0;
  }

  isSectorLeader(stock: SwingStock): boolean {
    return this.sectorLeaderSymbols.has(stock.symbol.toUpperCase());
  }

  refreshData(forceRefresh = false): void {
    this.loadSwingData(forceRefresh);
    this.loadBreakoutData(forceRefresh);
    this.loadSectorHeatmapData(forceRefresh);
    this.loadSectorRotationData();
    this.loadSectorLeaderData();
  }

  onRefreshClick(): void {
    this.refreshData(true);
  }

  setActiveTab(tab: ScreenerTab): void {
    this.activeTab = tab;
  }

  loadSwingData(forceRefresh = false): void {
    this.loading = true;
    this.error = '';

    this.swingService.getSwingScreen(forceRefresh).subscribe({
      next: (response) => {
        this.stocks = response.symbols ?? [];
        this.recomputeVisibleStocks();
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.error = 'Unable to load swing screener data. Make sure backend is running on :8000.';
        this.loading = false;
        this.cdr.markForCheck();
      },
    });
  }

  loadSectorHeatmapData(forceRefresh = false): void {
    this.sectorHeatmapLoading = true;
    this.sectorHeatmapError = '';

    this.heatmapService.getSectorHeatmap(forceRefresh, this.selectedSectorPeriod).subscribe({
      next: (response) => {
        this.sectorHeatmapSectors = response ?? [];
        this.sectorHeatmapLoading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.sectorHeatmapError = 'Unable to load sector heatmap data. Make sure backend is running on :8000.';
        this.sectorHeatmapLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  loadSectorRotationData(): void {
    this.sectorRotationLoading = true;
    this.sectorRotationError = '';

    this.heatmapService.getSectorRotationRanks().subscribe({
      next: (response) => {
        this.sectorRotationRanks = response ?? [];
        this.sectorRotationLoading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.sectorRotationError = 'Unable to load sector rotation dashboard data. Make sure backend is running on :8000.';
        this.sectorRotationLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  trackBySector(_: number, item: SectorRotationRankItem): string {
    return item.sector;
  }

  loadSectorLeaderData(): void {
    this.heatmapService.getAllSectorLeaders(this.selectedSectorPeriod).subscribe({
      next: (response) => {
        this.sectorLeaderSymbols.clear();
        for (const stock of response ?? []) {
          if (stock.symbol) {
            this.sectorLeaderSymbols.add(stock.symbol.toUpperCase());
          }
        }
        if (this.sortOption === 'sectorLeader') {
          this.recomputeVisibleStocks();
        }
        this.cdr.markForCheck();
      },
      error: () => {
        this.sectorLeaderSymbols.clear();
        this.cdr.markForCheck();
      },
    });
  }

  onSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.searchQuery = target.value;
    this.recomputeVisibleStocks();
  }

  onSortChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.sortOption = target.value as SortOption;
    this.recomputeVisibleStocks();
  }

  onSectorPeriodChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.selectedSectorPeriod = target.value as SectorPeriodOption;
    this.loadSectorHeatmapData(true);
    this.loadSectorLeaderData();
  }

  onScoreFilterChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    this.scoreFilterOption = target.value as ScoreFilterOption;
    this.recomputeVisibleStocks();
  }

  onShowMoreStocks(): void {
    this.showAllStocks = true;
    this.updateDisplayedStocks();
  }

  onShowLessStocks(): void {
    this.showAllStocks = false;
    this.updateDisplayedStocks();
  }

  private recomputeVisibleStocks(): void {
    const query = this.searchQuery.trim().toLowerCase();
    const minScore = this.scoreFilterOption === 'all' ? null : Number(this.scoreFilterOption);

    const filtered = this.stocks.filter((stock) => {
      const matchesSearch = !query || stock.symbol.toLowerCase().includes(query);
      const matchesScore = minScore === null || stock.total_score >= minScore;
      if (!matchesSearch) {
        return false;
      }

      return matchesScore;
    });

    this.visibleStocks = [...filtered].sort((a, b) => {
      switch (this.sortOption) {
        case 'scoreAsc':
          return a.total_score - b.total_score;
        case 'symbolAsc':
          return a.symbol.localeCompare(b.symbol);
        case 'symbolDesc':
          return b.symbol.localeCompare(a.symbol);
        case 'promoterHolding':
          const aHasPromoter = this.hasIncreasedPromoterHolding(a) ? 1 : 0;
          const bHasPromoter = this.hasIncreasedPromoterHolding(b) ? 1 : 0;
          if (bHasPromoter !== aHasPromoter) {
            return bHasPromoter - aHasPromoter;
          }
          return b.total_score - a.total_score;
        case 'breakoutOverlap':
          const aHasBreakout = this.hasBreakoutOverlap(a) ? 1 : 0;
          const bHasBreakout = this.hasBreakoutOverlap(b) ? 1 : 0;
          if (bHasBreakout !== aHasBreakout) {
            return bHasBreakout - aHasBreakout;
          }
          return b.total_score - a.total_score;
        case 'sectorLeader':
          const aIsSectorLeader = this.isSectorLeader(a) ? 1 : 0;
          const bIsSectorLeader = this.isSectorLeader(b) ? 1 : 0;
          if (bIsSectorLeader !== aIsSectorLeader) {
            return bIsSectorLeader - aIsSectorLeader;
          }
          return b.total_score - a.total_score;
        case 'scoreDesc':
        default:
          return b.total_score - a.total_score;
      }
    });

    this.showAllStocks = false;
    this.updateDisplayedStocks();

    if (!this.visibleStocks.length) {
      this.avgScore = 0;
      return;
    }

    const total = this.visibleStocks.reduce((sum, stock) => sum + stock.total_score, 0);
    this.avgScore = Math.round(total / this.visibleStocks.length);
  }

  private updateDisplayedStocks(): void {
    this.hasMoreSwingStocks = this.visibleStocks.length > this.defaultVisibleStocksCount;
    if (this.showAllStocks || !this.hasMoreSwingStocks) {
      this.displayedStocks = this.visibleStocks;
      return;
    }

    this.displayedStocks = this.visibleStocks.slice(0, this.defaultVisibleStocksCount);
  }

  private setSwingChartPoints(points: StockHistoryPoint[]): void {
    const validPoints = points.filter((point) => {
      const close = Number(point.close);
      return Number.isFinite(close);
    });

    this.swingChartPoints = validPoints;
    this.hasSwingChartData = validPoints.length > 1;
    this.swingChartStartDate = validPoints[0]?.date ?? '-';
    this.swingChartEndDate = validPoints.at(-1)?.date ?? '-';
    this.swingChartLatestClose = Number(validPoints.at(-1)?.close) || 0;

    if (!validPoints.length) {
      this.swingChartLow = 0;
      this.swingChartHigh = 0;
      this.swingChartPolylinePoints = '';
      return;
    }

    const closes = validPoints.map((point) => Number(point.close));
    const minClose = Math.min(...closes);
    const maxClose = Math.max(...closes);
    this.swingChartLow = minClose;
    this.swingChartHigh = maxClose;

    if (validPoints.length < 2) {
      this.swingChartPolylinePoints = '';
      return;
    }

    const viewWidth = 960;
    const viewHeight = 320;
    const paddingX = 20;
    const paddingY = 20;
    const closeRange = Math.max(maxClose - minClose, 1);

    this.swingChartPolylinePoints = validPoints
      .map((point, index) => {
        const x = paddingX + (index / (validPoints.length - 1)) * (viewWidth - paddingX * 2);
        const close = Number(point.close);
        const y = viewHeight - paddingY - ((close - minClose) / closeRange) * (viewHeight - paddingY * 2);
        return `${x.toFixed(2)},${y.toFixed(2)}`;
      })
      .join(' ');
  }

  scoreLabel(score: number): string {
    if (score >= 90) {
      return 'Excellent';
    }

    if (score >= 80) {
      return 'Strong';
    }

    return 'Watchlist';
  }

  formatCriterionValue(value: number | null): string {
    if (value === null || Number.isNaN(value)) {
      return 'N/A';
    }

    return Number.isInteger(value) ? `${value}` : value.toFixed(2);
  }

  formatCriterionDisplay(criterion: SwingCriterionScore): string {
    return `${this.formatCriterionValue(criterion.actual_value)} ${criterion.operator} ${this.formatCriterionValue(criterion.threshold)}`;
  }

  isCriterionPass(criterion: SwingCriterionScore): boolean {
    return criterion.score > 0;
  }

  loadBacktestData(): void {
    this.backtestLoading = true;
    this.backtestError = '';

    this.swingService.getTopStrategies().subscribe({
      next: (results) => {
        this.topStrategies = results ?? [];
        this.backtestLoading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.backtestError = 'Unable to load backtest results. Make sure backend is running on :8000.';
        this.backtestLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  runBacktestAnalysis(): void {
    this.backtestRunning = true;
    this.backtestError = '';

    this.swingService.runBacktest().subscribe({
      next: () => {
        this.backtestRunning = false;
        this.loadBacktestData();
        this.cdr.markForCheck();
      },
      error: () => {
        this.backtestError = 'Failed to run backtest. Please try again.';
        this.backtestRunning = false;
        this.cdr.markForCheck();
      },
    });
  }

  trackByBacktestSymbol(_: number, result: BacktestResult): string {
    return result.symbol;
  }

  getMetricClass(metric: string, value: number): string {
    switch (metric) {
      case 'win_rate':
        return value >= 60 ? 'metric-excellent' : value >= 50 ? 'metric-good' : 'metric-poor';
      case 'profit_factor':
        return value >= 2 ? 'metric-excellent' : value >= 1.5 ? 'metric-good' : 'metric-poor';
      case 'cagr':
        return value >= 20 ? 'metric-excellent' : value >= 10 ? 'metric-good' : 'metric-poor';
      case 'max_drawdown':
        return value >= -10 ? 'metric-excellent' : value >= -20 ? 'metric-good' : 'metric-poor';
      default:
        return '';
    }
  }

  onSymbolBacktestInput(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.symbolBacktestInput = target.value.toUpperCase();
  }

  runSymbolBacktest(): void {
    const symbol = this.symbolBacktestInput.trim();
    if (!symbol) {
      this.symbolBacktestError = 'Please enter a symbol';
      return;
    }

    this.symbolBacktestLoading = true;
    this.symbolBacktestError = '';
    this.symbolBacktestResult = null;

    this.swingService.backtestSymbol(symbol).subscribe({
      next: (result) => {
        if (result.error) {
          this.symbolBacktestError = result.error;
          this.symbolBacktestResult = null;
        } else {
          this.symbolBacktestResult = result;
        }
        this.symbolBacktestLoading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.symbolBacktestError = `Failed to backtest ${symbol}. Please check if the symbol exists.`;
        this.symbolBacktestLoading = false;
        this.cdr.markForCheck();
      },
    });
  }

  clearSymbolBacktest(): void {
    this.symbolBacktestInput = '';
    this.symbolBacktestResult = null;
    this.symbolBacktestError = '';
    this.showAllTrades = false;
  }

  getDisplayedTrades() {
    if (!this.symbolBacktestResult?.trades_list) {
      return [];
    }
    return this.showAllTrades 
      ? this.symbolBacktestResult.trades_list 
      : this.symbolBacktestResult.trades_list.slice(0, 10);
  }

  toggleShowAllTrades(): void {
    this.showAllTrades = !this.showAllTrades;
  }

  formatExitReason(reason: string): string {
    const reasonMap: Record<string, string> = {
      'stop_loss': 'Stop Loss',
      'trailing_stop': 'Trailing Stop',
      'max_holding': 'Max Hold'
    };
    return reasonMap[reason] || reason;
  }
}


