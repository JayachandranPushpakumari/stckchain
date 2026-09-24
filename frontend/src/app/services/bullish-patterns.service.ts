import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export interface BullishPatternStock {
  symbol: string;
  fundamental_score: number;
  current_price: number;
  as_of_date: string;
  patterns: string[];
  reasons: string[];
}

export interface BullishPatternResponse {
  generated_at: string;
  fundamental_candidates: number;
  matched_stocks: number;
  stocks: BullishPatternStock[];
}

@Injectable({ providedIn: 'root' })
export class BullishPatternsService {
  constructor(private readonly http: HttpClient) {}

  scan(): Observable<BullishPatternResponse> {
    return this.http.get<BullishPatternResponse>(`${environment.apiUrl}/screen/bullish-patterns`);
  }
}
