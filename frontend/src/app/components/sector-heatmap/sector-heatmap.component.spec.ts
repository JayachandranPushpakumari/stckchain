import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SectorHeatmapComponent } from './sector-heatmap.component';

describe('SectorHeatmapComponent', () => {
  let component: SectorHeatmapComponent;
  let fixture: ComponentFixture<SectorHeatmapComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SectorHeatmapComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SectorHeatmapComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
