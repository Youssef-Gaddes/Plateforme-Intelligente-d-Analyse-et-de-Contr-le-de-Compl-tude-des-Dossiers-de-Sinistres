import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

interface AuthResponse {
  access_token: string;
  token_type: string;
}

@Component({
  standalone: true,
  selector: 'app-auth',
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="auth-page">
      <div class="auth-card">
        <div class="auth-top-bar">
          <div>
            <p class="eyebrow">Assurance claims</p>
            <h1>{{ modeLabel() }}</h1>
            <p class="subtitle">Securely access your claims dashboard and upload documents for OCR processing.</p>
          </div>
          <div class="toggle-row" role="tablist" aria-label="Authentication mode">
            <button type="button" class="tab-button" (click)="setMode('login')" [class.active]="mode() === 'login'">Login</button>
            <button type="button" class="tab-button" (click)="setMode('register')" [class.active]="mode() === 'register'">Register</button>
          </div>
        </div>

        <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
          <div class="field-row" *ngIf="mode() === 'register'">
            <label for="name">Name</label>
            <input id="name" type="text" formControlName="name" placeholder="Your full name" />
            <small *ngIf="form.controls.name.invalid && form.controls.name.touched" class="error">Name is required.</small>
          </div>

          <div class="field-row">
            <label for="email">Email</label>
            <input id="email" type="email" formControlName="email" placeholder="name@example.com" />
            <small *ngIf="form.controls.email.invalid && form.controls.email.touched" class="error">Enter a valid email.</small>
          </div>

          <div class="field-row">
            <label for="password">Password</label>
            <input id="password" type="password" formControlName="password" placeholder="Enter your password" />
            <small *ngIf="form.controls.password.invalid && form.controls.password.touched" class="error">Password is required.</small>
          </div>

          <div class="field-row" *ngIf="mode() === 'register'">
            <label for="role">Role</label>
            <select id="role" formControlName="role">
              <option value="gestionnaire">Gestionnaire</option>
              <option value="lecteur">Lecteur</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <button class="primary-btn" type="submit" [disabled]="form.invalid || loading()">
            {{ modeButtonLabel() }}
          </button>

          <p class="helper-line">
            {{ helperText() }}
            <button type="button" class="link-btn" (click)="toggleMode()">{{ switchLabel() }}</button>
          </p>

          <div class="message" [class.error]="errorMessage()" [class.success]="successMessage()">
            <span *ngIf="errorMessage()">{{ errorMessage() }}</span>
            <span *ngIf="successMessage()">{{ successMessage() }}</span>
          </div>
        </form>
      </div>
    </section>
  `,
  styles: [
    `
      :host {
        display: block;
        min-height: 100vh;
        background: radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 28%),
          linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
      }
      .auth-page {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1.5rem;
      }
      .auth-card {
        width: min(540px, 100%);
        background: #ffffff;
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 28px;
        box-shadow: 0 40px 120px rgba(15, 23, 42, 0.08);
        padding: 2rem;
      }
      .auth-top-bar {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin-bottom: 1.75rem;
      }
      .eyebrow {
        margin: 0;
        font-size: 0.8125rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #2563eb;
      }
      h1 {
        margin: 0;
        font-size: 2rem;
        line-height: 1.1;
        color: #0f172a;
      }
      .subtitle {
        margin: 0.75rem 0 0;
        color: #475569;
        max-width: 36rem;
      }
      .toggle-row {
        display: flex;
        gap: 0.5rem;
        background: #f8fafc;
        border-radius: 999px;
        padding: 0.25rem;
        width: max-content;
      }
      .tab-button {
        border: 0;
        border-radius: 999px;
        background: transparent;
        color: #475569;
        padding: 0.75rem 1.25rem;
        font-weight: 600;
        cursor: pointer;
        transition: 0.2s ease;
      }
      .tab-button.active {
        background: #2563eb;
        color: #fff;
        box-shadow: 0 12px 24px rgba(37, 99, 235, 0.16);
      }
      form {
        display: grid;
        gap: 1rem;
      }
      .field-row {
        display: grid;
        gap: 0.5rem;
      }
      label {
        font-size: 0.9375rem;
        font-weight: 600;
        color: #1e293b;
      }
      input,
      select {
        width: 100%;
        min-height: 3rem;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 0.95rem 1rem;
        font: inherit;
        color: #0f172a;
        background: #f8fafc;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
      }
      input:focus,
      select:focus {
        outline: none;
        border-color: #2563eb;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
        background: #fff;
      }
      .primary-btn {
        width: 100%;
        min-height: 3.5rem;
        border: none;
        border-radius: 16px;
        background: linear-gradient(135deg, #2563eb, #9333ea);
        color: #fff;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 14px 30px rgba(37, 99, 235, 0.18);
      }
      .primary-btn:disabled {
        opacity: 0.65;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
      }
      .primary-btn:not(:disabled):hover {
        transform: translateY(-1px);
      }
      .helper-line {
        margin: 0;
        font-size: 0.9375rem;
        color: #64748b;
        display: flex;
        gap: 0.25rem;
        align-items: center;
        flex-wrap: wrap;
      }
      .link-btn {
        border: none;
        background: none;
        color: #2563eb;
        font-weight: 700;
        cursor: pointer;
        padding: 0;
      }
      .message {
        min-height: 1.5rem;
        font-size: 0.9375rem;
      }
      .message.error {
        color: #dc2626;
      }
      .message.success {
        color: #16a34a;
      }
      .error {
        color: #dc2626;
        font-size: 0.8125rem;
      }
      @media (max-width: 520px) {
        .auth-card {
          padding: 1.5rem;
        }
        .toggle-row {
          flex-wrap: wrap;
          justify-content: center;
        }
      }
    `
  ]
})
export class AuthComponent {
  private http = inject(HttpClient);
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private auth = inject(AuthService);

  mode = signal<'login' | 'register'>('login');
  loading = signal(false);
  errorMessage = signal('');
  successMessage = signal('');

  form = this.fb.group({
    name: [''],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
    role: ['gestionnaire', [Validators.required]],
  });

  constructor() {
    if (this.auth.isAuthenticated) {
      this.router.navigate(['/dashboard']);
    }
  }

  setMode(value: 'login' | 'register') {
    this.mode.set(value);
    this.resetMessages();
  }

  toggleMode() {
    this.setMode(this.mode() === 'login' ? 'register' : 'login');
  }

  modeLabel() {
    return this.mode() === 'login' ? 'Welcome back' : 'Create your account';
  }

  modeButtonLabel() {
    return this.mode() === 'login' ? 'Sign in' : 'Create account';
  }

  helperText() {
    return this.mode() === 'login' ? "Don't have an account?" : 'Already have an account?';
  }

  switchLabel() {
    return this.mode() === 'login' ? 'Register' : 'Login';
  }

  submit() {
    this.errorMessage.set('');
    this.successMessage.set('');
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    const payload = this.mode() === 'login'
      ? { email: this.form.value.email, password: this.form.value.password }
      : { name: this.form.value.name, email: this.form.value.email, password: this.form.value.password, role: this.form.value.role };

    const endpoint = this.mode() === 'login' ? '/auth/login' : '/auth/register';

    this.http.post<AuthResponse>('http://localhost:8000' + endpoint, payload).subscribe({
      next: (result) => {
        if (this.mode() === 'login') {
          this.auth.setToken(result.access_token);
          this.router.navigate(['/dashboard']);
        } else {
          this.successMessage.set('Account created successfully. You may now sign in.');
          this.setMode('login');
        }
        this.loading.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.errorMessage.set(error.error?.detail || 'Unable to complete request. Please try again.');
        this.loading.set(false);
      }
    });
  }

  private resetMessages() {
    this.errorMessage.set('');
    this.successMessage.set('');
  }
}
