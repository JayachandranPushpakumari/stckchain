import { CommonModule } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, OnInit } from '@angular/core';

import { BullishStructureResponse, BullishStructureStock, BullishStructuresService } from '../../services/bullish-structures.service';

@Component({
  selector: 'app-bullish-structures',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './bullish-structures.component.html',
  styleUrl: './bullish-structures.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BullishStructuresComponent implements OnInit {
  loading = true;
  error = '';
  result: BullishStructureResponse | null = null;

  constructor(
    private readonly service: BullishStructuresService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.load();
  }

  load(forceRefresh = false): void {
    this.loading = true;
    this.error = '';
    const request = forceRefresh ? this.service.refresh() : this.service.scan();
    request.subscribe({
      next: (result) => {
        this.result = result;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.error = 'Unable to scan bullish structures.';
        this.loading = false;
        this.cdr.markForCheck();
      },
    });
  }

  trackBySymbol(_: number, stock: BullishStructureStock): string {
    return stock.symbol;
  }
}
