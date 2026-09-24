import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { BreakoutDiagnosticsRun, OpportunityRun } from '../models/opportunity';

@Injectable({ providedIn: 'root' })
export class OpportunitiesService {
  private readonly endpoint = `${environment.apiUrl}/internal/opportunities`;

  constructor(private readonly http: HttpClient) {}

  getLatest(): Observable<OpportunityRun> {
    return this.http.get<OpportunityRun>(`${this.endpoint}/latest`);
  }

  runBreakoutPipeline(): Observable<OpportunityRun> {
    return this.http.post<OpportunityRun>(`${this.endpoint}/breakout/run`, {});
  }

  getBreakoutDiagnostics(): Observable<BreakoutDiagnosticsRun> {
    return this.http.get<BreakoutDiagnosticsRun>(`${this.endpoint}/breakout/diagnostics`);
  }
}
