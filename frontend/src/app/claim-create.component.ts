import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
}

interface Claim {
  id: number;
  claim_number: string;
  insured_name: string;
  status: string;
  claim_type: string;
  completeness_score?: number;
}

@Component({
  standalone: true,
  selector: 'app-claim-create',
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="page-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">Créer une déclaration</p>
          <h1>Ajouter un nouveau sinistre</h1>
          <p class="lead">Les administrateurs et gestionnaires peuvent créer un sinistre et l'affecter à un lecteur.</p>
        </div>
        <button class="ghost-btn" (click)="navigateHome()">Retour au tableau de bord</button>
      </header>

      <section class="panel form-panel">
        <form [formGroup]="form" (ngSubmit)="submit()">
          <div class="field-row">
            <label for="claim_number">Numéro de déclaration</label>
            <input id="claim_number" formControlName="claim_number" placeholder="ALZ-55120984" />
            <small *ngIf="form.controls.claim_number.invalid && form.controls.claim_number.touched" class="error">Le numéro de déclaration est requis.</small>
          </div>

          <div class="field-row">
            <label for="insured_name">Nom assuré</label>
            <input id="insured_name" formControlName="insured_name" placeholder="Jean Dupont" />
            <small *ngIf="form.controls.insured_name.invalid && form.controls.insured_name.touched" class="error">Le nom de l'assuré est requis.</small>
          </div>

          <div class="field-grid">
            <div class="field-row">
              <label for="status">Statut</label>
              <select id="status" formControlName="status">
                <option value="ouvert">Ouvert</option>
                <option value="en_cours">En cours</option>
                <option value="ferme">Fermé</option>
              </select>
            </div>

            <div class="field-row">
              <label for="claim_type">Type de sinistre</label>
              <select id="claim_type" formControlName="claim_type">
                <option value="auto">Auto</option>
                <option value="habitation">Habitation</option>
                <option value="sante">Santé</option>
              </select>
            </div>
          </div>

          <div class="field-row">
            <label for="user_id">Lecteur assigné</label>
            <select id="user_id" formControlName="user_id">
              <option *ngFor="let user of lecteurs()" [value]="user.id">
                {{ user.name }} ({{ user.email }})
              </option>
            </select>
            <small *ngIf="lecteurs().length === 0" class="error">Aucun lecteur disponible. Créez d'abord un lecteur.</small>
          </div>

          <button class="primary-btn" type="submit" [disabled]="form.invalid || loading() || lecteurs().length === 0">
            Créer
          </button>

          <div class="message" [class.error]="errorMessage()" [class.success]="successMessage()">
            <span *ngIf="errorMessage()">{{ errorMessage() }}</span>
            <span *ngIf="successMessage()">{{ successMessage() }}</span>
          </div>
        </form>
      </section>
    </div>
  `,
  styles: [
    `
      :host {
        display: block;
        min-height: 100vh;
        background: linear-gradient(180deg, #f8fbff 0%, #eef4ff 100%);
        padding: 2rem;
      }
      .page-shell {
        width: min(1140px, 100%);
        margin: 0 auto;
        display: grid;
        gap: 1.5rem;
      }
      .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 1.75rem 2rem;
        border-radius: 28px;
        background: #ffffff;
        box-shadow: 0 30px 70px rgba(15, 23, 42, 0.08);
      }
      .eyebrow {
        margin: 0 0 0.5rem;
        color: #2563eb;
        font-size: 0.8125rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
      }
      h1 {
        margin: 0;
        font-size: clamp(2rem, 2.5vw, 2.5rem);
        line-height: 1.05;
        color: #0f172a;
      }
      .lead {
        margin: 0.75rem 0 0;
        color: #475569;
      }
      .ghost-btn {
        border: 1px solid rgba(15, 23, 42, 0.12);
        background: #ffffff;
        color: #0f172a;
        border-radius: 16px;
        padding: 1rem 1.25rem;
        font-weight: 700;
        cursor: pointer;
      }
      .panel {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 28px;
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.06);
      }
      .form-panel {
        max-width: 620px;
      }
      .field-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
      }
      .field-row {
        display: grid;
        gap: 0.5rem;
        margin-bottom: 1rem;
      }
      label {
        font-weight: 700;
        color: #0f172a;
      }
      input,
      select {
        width: 100%;
        min-height: 3rem;
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        background: #f8fafc;
        color: #0f172a;
        font: inherit;
      }
      input:focus,
      select:focus {
        border-color: #2563eb;
        outline: none;
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
        font-weight: 700;
        cursor: pointer;
      }
      .primary-btn:disabled {
        opacity: 0.65;
        cursor: not-allowed;
      }
      .message {
        min-height: 1.25rem;
        margin-top: 0.75rem;
      }
      .message.error {
        color: #dc2626;
      }
      .message.success {
        color: #16a34a;
      }
      .error {
        color: #dc2626;
        font-size: 0.875rem;
      }
    `
  ]
})
export class ClaimCreateComponent {
  private fb = inject(FormBuilder);
  private http = inject(HttpClient);
  private router = inject(Router);
  private auth = inject(AuthService);

  loading = signal(false);
  errorMessage = signal('');
  successMessage = signal('');
  lecteurs = signal<User[]>([]);

  form = this.fb.group({
    claim_number: ['', [Validators.required]],
    insured_name: ['', [Validators.required]],
    status: ['ouvert', [Validators.required]],
    claim_type: ['auto', [Validators.required]],
    user_id: this.fb.control<number | null>(null, Validators.required),
  });

  constructor() {
    if (!this.auth.isAuthenticated || !['admin', 'gestionnaire'].includes(this.auth.role() ?? '')) {
      this.router.navigate(['/dashboard']);
      return;
    }
    this.loadLecteurs();
  }

  loadLecteurs() {
    this.http.get<User[]>('http://localhost:8000/users?role=lecteur', this.auth.authOptions).subscribe({
      next: (users) => {
        this.lecteurs.set(users);
        if (users.length) {
          this.form.get('user_id')?.setValue(users[0].id);
        }
      },
      error: () => {
        this.lecteurs.set([]);
      },
    });
  }

  submit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');

    this.http.post<Claim>('http://localhost:8000/claims', this.form.value, this.auth.authOptions).subscribe({
      next: () => {
        this.successMessage.set('Sinistre créé avec succès.');
        this.loading.set(false);
        this.router.navigate(['/claims']);
      },
      error: () => {
        this.errorMessage.set('Impossible de créer le sinistre. Vérifiez les informations et réessayez.');
        this.loading.set(false);
      }
    });
  }

  navigateHome() {
    this.router.navigate(['/dashboard']);
  }
}
