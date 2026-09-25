import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';

import { BullishPatternResponse, BullishPatternStock, BullishPatternsService } from '../../services/bullish-patterns.service';

@Component({
  selector: 'app-bullish-patterns',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './bullish-patterns.component.html',
  styleUrl: './bullish-patterns.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BullishPatternsComponent implements OnInit {
  loading = true;
  error = '';
  result: BullishPatternResponse | null = null;

  constructor(
    private readonly service: BullishPatternsService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.loadCached();
  }

  loadCached(): void {
    this.loading = true;
    this.error = '';
    this.service.getCached().subscribe({
      next: (result) => {
        this.result = result;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.error = 'Unable to load bullish chart patterns.';
        this.loading = false;
        this.cdr.markForCheck();
      },
    });
  }

  refresh(): void {
    if (!globalThis.confirm('Refresh bullish pattern scan? This recomputes patterns for the entire fundamental universe.')) {
      return;
    }
    this.loading = true;
    this.error = '';
    this.service.refresh().subscribe({
      next: (result) => {
        this.result = result;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.error = 'Unable to refresh bullish chart patterns.';
        this.loading = false;
        this.cdr.markForCheck();
      },
    });
  }

  trackBySymbol(_: number, stock: BullishPatternStock): string {
    return stock.symbol;
  }
}
