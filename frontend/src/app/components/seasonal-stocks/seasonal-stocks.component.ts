import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { SeasonalityService } from '../../services/seasonality.service';

interface SeasonalSectorSummary {
  sector: string;
  stockCount: number;
  avgCombinedScore: number;
  avgWinRate: number;
  avgMedianReturn: number;
  sectorScore: number;
}

@Component({
  selector: 'app-seasonal-stocks',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './seasonal-stocks.component.html',
  styleUrls: ['./seasonal-stocks.component.css']
})
export class SeasonalStocksComponent implements OnInit {

  stocks: any[] = [];
  bestSectors: SeasonalSectorSummary[] = [];
  selectedSector = '';
  loading = false;
  error = '';

  selectedMonth = new Date().getMonth() + 1;

  months = [
    { id:1, name:'January' },
    { id:2, name:'February' },
    { id:3, name:'March' },
    { id:4, name:'April' },
    { id:5, name:'May' },
    { id:6, name:'June' },
    { id:7, name:'July' },
    { id:8, name:'August' },
    { id:9, name:'September' },
    { id:10, name:'October' },
    { id:11, name:'November' },
    { id:12, name:'December' }
  ];

  constructor(
    private seasonalityService: SeasonalityService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {

    this.loading = true;
    this.error = '';

    this.seasonalityService
      .getSeasonalStocks(Number(this.selectedMonth))
      .subscribe({
        next: (data) => {
          this.stocks = Array.isArray(data) ? data : [];
          this.bestSectors = this.calculateBestSectors(this.stocks);
          this.selectedSector = '';
          this.loading = false;
          this.cdr.markForCheck();
        },
        error: (err) => {
          console.error(err);
          this.error = 'Unable to load seasonal stocks.';
          this.stocks = [];
          this.bestSectors = [];
          this.loading = false;
          this.cdr.markForCheck();
        }
      });
  }

  get availableSectors(): string[] {
    const seen = new Set<string>();
    for (const s of this.stocks) {
      if (s.sector) seen.add(s.sector);
    }
    return Array.from(seen).sort();
  }

  get filteredStocks(): any[] {
    if (!this.selectedSector) return this.stocks;
    return this.stocks.filter(s => s.sector === this.selectedSector);
  }

  getBestSectors(): SeasonalSectorSummary[] {
    return this.calculateBestSectors(this.stocks);
  }

  private calculateBestSectors(stocks: any[]): SeasonalSectorSummary[] {
    const sectorMap = new Map<string, { count: number; combinedScore: number; winRate: number; medianReturn: number }>();

    for (const stock of stocks) {
      const sector = stock.sector;
      if (!sector) {
        continue;
      }

      const current = sectorMap.get(sector) ?? { count: 0, combinedScore: 0, winRate: 0, medianReturn: 0 };
      current.count += 1;
      current.combinedScore += Number(stock.combined_score ?? 0);
      current.winRate += Number(stock.win_rate ?? 0);
      current.medianReturn += Number(stock.median_return ?? 0);
      sectorMap.set(sector, current);
    }

    const maxStockCount = Math.max(...Array.from(sectorMap.values()).map((values) => values.count));

    return Array.from(sectorMap.entries())
      .map(([sector, values]) => {
        const avgCombinedScore = values.combinedScore / values.count;
        const avgWinRate = values.winRate / values.count;
        const avgMedianReturn = values.medianReturn / values.count;
        const stockCountScore = (values.count / maxStockCount) * 100;
        const sectorScore = (stockCountScore * 0.45) + (avgWinRate * 0.4) + (avgCombinedScore * 0.15);

        return {
          sector,
          stockCount: values.count,
          avgCombinedScore: Number(avgCombinedScore.toFixed(2)),
          avgWinRate: Number(avgWinRate.toFixed(2)),
          avgMedianReturn: Number(avgMedianReturn.toFixed(2)),
          sectorScore: Number(sectorScore.toFixed(2)),
        };
      })
      .sort((a, b) => {
        if (b.sectorScore !== a.sectorScore) {
          return b.sectorScore - a.sectorScore;
        }
        if (b.stockCount !== a.stockCount) {
          return b.stockCount - a.stockCount;
        }
        if (b.avgWinRate !== a.avgWinRate) {
          return b.avgWinRate - a.avgWinRate;
        }
        return b.avgMedianReturn - a.avgMedianReturn;
      })
      .slice(0, 5);
  }

}