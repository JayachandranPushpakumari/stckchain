import { TestBed } from '@angular/core/testing';

import { SeasonalityService } from './seasonality.service';

describe('SeasonalityService', () => {
  let service: SeasonalityService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(SeasonalityService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
