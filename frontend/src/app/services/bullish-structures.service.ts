import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export interface BullishStructureStock {
  symbol: string;
  fundamental_score: number;
  structure_type: string;
  structure_label: string;
  lower_band: number;
  upper_band: number;
  band_position: number;
  lower_touches: number;
  upper_touches: number;
  rsi: number;
  macd_improving: boolean;
  current_price: number;
  entry_low: number;
  entry_high: number;
  stop_loss: number;
  target_1: number;
  target_2: number;
  risk_reward: number;
  as_of_date: string;
  reasons: string[];
}

export interface BullishStructureResponse {
  generated_at: string;
  fundamental_candidates: number;
  matched_stocks: number;
  stocks: BullishStructureStock[];
}

@Injectable({ providedIn: 'root' })
export class BullishStructuresService {
  constructor(private readonly http: HttpClient) {}

  scan(): Observable<BullishStructureResponse> {
    return this.http.get<BullishStructureResponse>(`${environment.apiUrl}/screen/bullish-structures`);
  }

  refresh(): Observable<BullishStructureResponse> {
    return this.http.post<BullishStructureResponse>(`${environment.apiUrl}/screen/bullish-structures/refresh`, {});
  }
}
