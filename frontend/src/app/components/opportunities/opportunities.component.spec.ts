import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { OpportunitiesService } from '../../services/opportunities.service';
import { OpportunitiesComponent } from './opportunities.component';

const run = {
  run_id: 1,
  generated_at: '2026-09-23T00:00:00Z',
  setup_type: 'BREAKOUT',
  market_regime: 'WEAK' as const,
  stage_counts: {
    all_stocks: 2680,
    data_quality: 2212,
    liquidity: 1162,
    fundamentals: 495,
    breakout: 0,
    market_regime: 0,
    risk_reward: 0,
    high_confidence: 0,
  },
  minimum_score: 85,
  message: 'No high-confidence opportunities today.',
  opportunities: [],
};

describe('OpportunitiesComponent', () => {
  let component: OpportunitiesComponent;
  let fixture: ComponentFixture<OpportunitiesComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [OpportunitiesComponent],
      providers: [{
        provide: OpportunitiesService,
        useValue: { getLatest: () => of(run), runBreakoutPipeline: () => of(run) },
      }],
    }).compileComponents();

    fixture = TestBed.createComponent(OpportunitiesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('shows the latest strict no-opportunity result', () => {
    expect(component.regime).toBe('WEAK');
    expect(component.stageCount('fundamentals')).toBe(495);
    expect(fixture.nativeElement.textContent).toContain('No high-confidence opportunities today.');
  });
});
