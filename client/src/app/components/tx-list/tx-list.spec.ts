import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TxList } from './tx-list';

describe('TxList', () => {
  let component: TxList;
  let fixture: ComponentFixture<TxList>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TxList]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TxList);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
