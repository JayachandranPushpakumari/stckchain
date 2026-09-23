import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { OpportunitiesService } from './opportunities.service';

describe('OpportunitiesService', () => {
  let service: OpportunitiesService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(OpportunitiesService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('loads the latest persisted run', () => {
    service.getLatest().subscribe();
    const request = http.expectOne(`${environment.apiUrl}/internal/opportunities/latest`);
    expect(request.request.method).toBe('GET');
    request.flush({ market_regime: 'WEAK', message: null, opportunities: [] });
  });

  it('runs and persists the breakout pipeline', () => {
    service.runBreakoutPipeline().subscribe();
    const request = http.expectOne(`${environment.apiUrl}/internal/opportunities/breakout/run`);
    expect(request.request.method).toBe('POST');
    request.flush({ market_regime: 'BULL', message: null, opportunities: [] });
  });
});
