import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SendForm } from './send-form';

describe('SendForm', () => {
  let component: SendForm;
  let fixture: ComponentFixture<SendForm>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SendForm]
    })
    .compileComponents();

    fixture = TestBed.createComponent(SendForm);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
