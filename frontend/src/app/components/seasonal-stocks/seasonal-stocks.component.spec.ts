import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SeasonalStocksComponent } from './seasonal-stocks.component';

describe('SeasonalStocksComponent', () => {
  let component: SeasonalStocksComponent;
  let fixture: ComponentFixture<SeasonalStocksComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SeasonalStocksComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SeasonalStocksComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
