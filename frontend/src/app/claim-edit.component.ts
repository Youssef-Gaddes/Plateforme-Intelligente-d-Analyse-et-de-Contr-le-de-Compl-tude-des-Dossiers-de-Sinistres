import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { Router, ActivatedRoute } from '@angular/router';
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
  user_id?: number;
}

@Component({
  standalone: true,
  selector: 'app-claim-edit',
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="page-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">Modifier une déclaration</p>
          <h1>Mettre à jour le sinistre</h1>
          <p class="lead">Modifiez un sinistre existant et affectez-le au lecteur approprié.</p>
        </div>
        <button class="ghost-btn" (click)="navigateHome()">Retour à la liste</button>
      </header>

      <section class="panel form-panel" *ngIf="claim(); else loading">
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
              <option value="" disabled>Sélectionnez un lecteur</option>
              <option *ngFor="let user of lecteurs()" [value]="user.id">{{ user.name }} ({{ user.email }})</option>
            </select>
            <small *ngIf="form.controls.user_id.invalid && form.controls.user_id.touched" class="error">Veuillez assigner un lecteur à cette déclaration.</small>
          </div>

          <button class="primary-btn" type="submit" [disabled]="form.invalid || saving()">
            Enregistrer
          </button>

          <div class="message" [class.error]="errorMessage()" [class.success]="successMessage()">
            <span *ngIf="errorMessage()">{{ errorMessage() }}</span>
            <span *ngIf="successMessage()">{{ successMessage() }}</span>
          </div>
        </form>
      </section>

      <ng-template #loading>
        <div class="loading-shell">
          <p>Loading claim information...</p>
        </div>
      </ng-template>
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
      .ghost-btn,
      .primary-btn {
        min-height: 3.25rem;
        border: none;
        border-radius: 16px;
        cursor: pointer;
        font-weight: 700;
        padding: 1rem 1.25rem;
      }
      .ghost-btn {
        background: #ffffff;
        color: #0f172a;
        border: 1px solid rgba(15, 23, 42, 0.12);
      }
      .primary-btn {
        background: linear-gradient(135deg, #2563eb, #9333ea);
        color: #fff;
      }
      .panel {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 28px;
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.06);
      }
      .form-panel {
        max-width: 700px;
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
        outline: none;
        border-color: #2563eb;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
        background: #fff;
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
      .loading-shell {
        padding: 3rem;
        border-radius: 28px;
        background: #ffffff;
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.06);
      }
    `
  ]
})
export class ClaimEditComponent {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private http = inject(HttpClient);
  private fb = inject(FormBuilder);
  private auth = inject(AuthService);

  claim = signal<Claim | null>(null);
  lecteurs = signal<User[]>([]);
  saving = signal(false);
  errorMessage = signal('');
  successMessage = signal('');

  form = this.fb.group({
    claim_number: ['', [Validators.required]],
    insured_name: ['', [Validators.required]],
    status: ['ouvert', [Validators.required]],
    claim_type: ['auto', [Validators.required]],
    user_id: [null as number | null, [Validators.required]],
  });

  constructor() {
    const role = this.auth.role();
    if (!this.auth.isAuthenticated || !['admin', 'gestionnaire'].includes(role ?? '')) {
      this.router.navigate(['/dashboard']);
      return;
    }

    const claimId = Number(this.route.snapshot.paramMap.get('id'));
    if (!claimId) {
      this.router.navigate(['/claims']);
      return;
    }

    this.loadClaim(claimId);
    this.loadLecteurs();
  }

  loadClaim(claimId: number) {
    this.http.get<Claim>(`http://localhost:8000/claims/${claimId}`, this.auth.authOptions).subscribe({
      next: (claim) => {
        this.claim.set(claim);
        this.form.setValue({
          claim_number: claim.claim_number,
          insured_name: claim.insured_name,
          status: claim.status,
          claim_type: claim.claim_type || 'auto',
          user_id: claim.user_id ?? null,
        } as { claim_number: string; insured_name: string; status: string; claim_type: string; user_id: number | null });
      },
      error: () => {
        this.router.navigate(['/claims']);
      },
    });
  }

  loadLecteurs() {
    this.http.get<User[]>('http://localhost:8000/users?role=lecteur', this.auth.authOptions).subscribe({
      next: (users) => this.lecteurs.set(users),
      error: () => this.lecteurs.set([]),
    });
  }

  submit() {
    if (this.form.invalid || !this.claim()) {
      this.form.markAllAsTouched();
      return;
    }

    this.saving.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');

    const claimId = this.claim()!.id;
    const body = {
      claim_number: this.form.controls.claim_number.value,
      insured_name: this.form.controls.insured_name.value,
      status: this.form.controls.status.value,
      claim_type: this.form.controls.claim_type.value,
      user_id: Number(this.form.controls.user_id.value),
    };

    this.http.put<Claim>(`http://localhost:8000/claims/${claimId}`, body, this.auth.authOptions).subscribe({
      next: () => {
        this.successMessage.set('Sinistre mis à jour avec succès.');
        this.saving.set(false);
      },
      error: (err) => {
        this.errorMessage.set(err.error?.detail || 'Impossible de mettre à jour le sinistre.');
        this.saving.set(false);
      },
    });
  }

  navigateHome() {
    this.router.navigate(['/claims']);
  }
}
