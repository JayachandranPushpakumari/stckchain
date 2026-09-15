import { ChangeDetectorRef, Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import { HeatmapService, SectorHeatmapItem, SectorLeaderItem } from '../../services/heatmap.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sector-heatmap',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sector-heatmap.component.html',
  styleUrls: ['./sector-heatmap.component.css']
})
export class SectorHeatmapComponent implements OnInit {

  @Input() sectors: SectorHeatmapItem[] = [];
  @Input() selectedPeriod = '3m';
  @ViewChild('sectorLeadersSection') sectorLeadersSection?: ElementRef<HTMLElement>;

  selectedSector = '';
  sectorLeaders: SectorLeaderItem[] = [];
  sectorLeadersLoading = false;
  sectorLeadersError = '';
  private sectorLeadersRequestId = 0;

  constructor(
    private heatmapService: HeatmapService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    if (this.sectors.length) {
      return;
    }

    this.heatmapService.getSectorHeatmap().subscribe({
      next: (data) => {
        this.sectors = data;
        this.cdr.markForCheck();
      },
      error: (err) => {
        console.error(err);
        this.cdr.markForCheck();
      }
    });
  }

  loadSectorLeaders(sector: string): void {

    const requestId = ++this.sectorLeadersRequestId;
    this.selectedSector = sector;
    this.sectorLeaders = [];
    this.sectorLeadersLoading = true;
    this.sectorLeadersError = '';
    this.cdr.markForCheck();
    setTimeout(() => this.scrollToSectorLeaders());

    this.heatmapService.getSectorLeaders(sector, this.selectedPeriod)
      .subscribe({
        next: (data) => {
          if (requestId !== this.sectorLeadersRequestId) {
            return;
          }

          this.sectorLeaders = data;
          this.sectorLeadersLoading = false;
          this.cdr.markForCheck();
        },
        error: (err) => {
          if (requestId !== this.sectorLeadersRequestId) {
            return;
          }

          console.error(err);
          this.sectorLeadersError = `Unable to load stocks for ${sector}.`;
          this.sectorLeadersLoading = false;
          this.cdr.markForCheck();
        }
      });
  }

  private scrollToSectorLeaders(): void {
    this.sectorLeadersSection?.nativeElement.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }

  getSectorStrengthClass(strength: number): string {
  if (strength >= 15) {
    return 'strong';
  }

  if (strength >= 0) {
    return 'medium';
  }

  return 'weak';
}

getStrengthWidth(strength: number): number {
  return Math.min(Math.abs(strength), 40) * 2.5;
}

}
