import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';

import { MarketRegime, OpportunityRun, StockChainOpportunity } from '../../models/opportunity';
import { OpportunitiesService } from '../../services/opportunities.service';

@Component({
  selector: 'app-opportunities',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './opportunities.component.html',
  styleUrl: './opportunities.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpportunitiesComponent implements OnInit {
  loading = true;
  running = false;
  error = '';
  run: OpportunityRun | null = null;

  readonly stages = [
    { key: 'all_stocks', label: 'All Stocks' },
    { key: 'data_quality', label: 'Data Quality' },
    { key: 'liquidity', label: 'Liquidity' },
    { key: 'fundamentals', label: 'Fundamentals' },
    { key: 'breakout', label: 'Breakout' },
    { key: 'market_regime', label: 'Market Regime' },
    { key: 'risk_reward', label: 'Risk / Reward' },
    { key: 'high_confidence', label: 'Final' },
  ] as const;

  constructor(
    private readonly opportunitiesService: OpportunitiesService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadLatest();
  }

  loadLatest(): void {
    this.loading = true;
    this.error = '';
    this.opportunitiesService.getLatest().subscribe({
      next: (run) => {
        this.run = run;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.error = 'Unable to load the latest StockChain opportunity run.';
        this.loading = false;
        this.cdr.markForCheck();
      },
    });
  }

  runPipeline(): void {
    if (!globalThis.confirm('Run the Breakout Opportunity pipeline now? This performs analysis and saves a new run.')) {
      return;
    }
    this.running = true;
    this.error = '';
    this.opportunitiesService.runBreakoutPipeline().subscribe({
      next: (run) => {
        this.run = run;
        this.running = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.error = 'The opportunity pipeline could not be completed. The previous result is still displayed.';
        this.running = false;
        this.cdr.markForCheck();
      },
    });
  }

  get regime(): MarketRegime {
    const value = this.run?.market_regime;
    return typeof value === 'string' ? value : value?.regime ?? 'UNKNOWN';
  }

  get regimeReason(): string {
    const value = this.run?.market_regime;
    return typeof value === 'object' ? value.reason : this.regimeExplanation(this.regime);
  }

  get breadth(): number | null {
    const value = this.run?.market_regime;
    return typeof value === 'object' && value.breadth !== undefined ? value.breadth ?? null : null;
  }

  stageCount(key: keyof NonNullable<OpportunityRun['stage_counts']>): number {
    return this.run?.stage_counts?.[key] ?? 0;
  }

  trackBySymbol(_: number, opportunity: StockChainOpportunity): string {
    return opportunity.symbol;
  }

  private regimeExplanation(regime: MarketRegime): string {
    const explanations: Record<MarketRegime, string> = {
      BULL: 'NIFTY trend and market breadth support new breakout opportunities.',
      NEUTRAL: 'Market conditions are mixed; strict Breakout V1 publication remains paused.',
      WEAK: 'Market participation is weak; strict Breakout V1 publication remains paused.',
      BEAR: 'Market conditions do not support new breakout opportunities.',
      UNKNOWN: 'NIFTY history is not sufficient to classify the market.',
    };
    return explanations[regime];
  }
}
