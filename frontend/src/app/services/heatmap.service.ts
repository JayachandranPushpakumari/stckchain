import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { Injectable } from '@angular/core';
import { Observable, of, tap } from 'rxjs';

export interface SectorHeatmapItem {
  sector: string;
  strength: number;
}

export interface SectorLeaderItem {
  symbol: string;
  sector: string;
  rs_score: number;
  total_score: number | null;
  rank: number;
}

export interface SectorRotationRankItem {
  sector: string;
  '1d'?: number;
  '1w'?: number;
  '1m'?: number;
  '3m'?: number;
  '6m'?: number;
  momentum_change: number;
  score: number;
}

interface SectorHeatmapCachePayload {
  timestamp: number;
  data: SectorHeatmapItem[];
}

@Injectable({
  providedIn: 'root'
})
export class HeatmapService {

  private readonly apiUrl = environment.apiUrl;
  private readonly sectorHeatmapCacheKey = 'stockchain_sector_heatmap_cache_v1';
  private readonly sectorHeatmapCacheTtlMs = 24 * 60 * 60 * 1000;

  constructor(private http: HttpClient) {}

  getSectorHeatmap(forceRefresh = false, period = '3m'): Observable<SectorHeatmapItem[]> {
    const cachedData = forceRefresh ? null : this.getCachedSectorHeatmapData(period);
    if (cachedData) {
      return of(cachedData);
    }

    return this.http.get<SectorHeatmapItem[]>(`${this.apiUrl}/heatmap/sectors?period=${encodeURIComponent(period)}`).pipe(
      tap((data) => this.setCachedSectorHeatmapData(data ?? [], period)),
    );
  }

  private getCachedSectorHeatmapData(period: string): SectorHeatmapItem[] | null {
    const raw = localStorage.getItem(this.getSectorHeatmapCacheKey(period));
    if (!raw) {
      return null;
    }

    try {
      const payload = JSON.parse(raw) as SectorHeatmapCachePayload;
      const isExpired = Date.now() - payload.timestamp > this.sectorHeatmapCacheTtlMs;
      if (isExpired) {
        localStorage.removeItem(this.getSectorHeatmapCacheKey(period));
        return null;
      }

      return Array.isArray(payload.data) ? payload.data : null;
    } catch {
      localStorage.removeItem(this.getSectorHeatmapCacheKey(period));
      return null;
    }
  }

  private setCachedSectorHeatmapData(data: SectorHeatmapItem[], period: string): void {
    const payload: SectorHeatmapCachePayload = {
      timestamp: Date.now(),
      data,
    };
    localStorage.setItem(this.getSectorHeatmapCacheKey(period), JSON.stringify(payload));
  }

  getSectorLeaders(sector: string, period = '3m'): Observable<SectorLeaderItem[]> {
    return this.http.get<SectorLeaderItem[]>(
      `${this.apiUrl}/leaders/sector/${encodeURIComponent(sector)}?period=${encodeURIComponent(period)}`
    );
  }

  getAllSectorLeaders(period = '3m'): Observable<SectorLeaderItem[]> {
    return this.http.get<SectorLeaderItem[]>(
      `${this.apiUrl}/leaders/sector-leaders?period=${encodeURIComponent(period)}`
    );
  }

  getSectorRotationRanks(): Observable<SectorRotationRankItem[]> {
    return this.http.get<SectorRotationRankItem[]>(
      `${this.apiUrl}/heatmap/sector-rotation`
    );
  }

  private getSectorHeatmapCacheKey(period: string): string {
    return `${this.sectorHeatmapCacheKey}_${period}`;
  }
}
