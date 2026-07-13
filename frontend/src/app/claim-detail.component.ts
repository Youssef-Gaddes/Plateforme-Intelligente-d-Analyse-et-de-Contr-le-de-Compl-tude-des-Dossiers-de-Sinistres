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

interface DocumentItem {
  id: number;
  claim_id: number;
  file_name: string;
  document_type?: string;
  classification_confidence?: number;
}

@Component({
  standalone: true,
  selector: 'app-claim-detail',
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="page-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">Détails du sinistre</p>
          <h1>{{ claim()?.claim_number || 'Chargement...' }}</h1>
          <p class="lead">Téléversez un document et vérifiez son type et sa confiance de classification.</p>
        </div>
        <button class="ghost-btn" (click)="navigateBack()">Retour aux sinistres</button>
      </header>

      <section class="panel">
        <div *ngIf="claim(); else loading">
          <div class="claim-summary">
            <div class="claim-info">
              <p><strong>Assuré :</strong> {{ claim()?.insured_name }}</p>
              <p><strong>Statut :</strong> {{ claim()?.status }}</p>
              <p><strong>Type :</strong> {{ claim()?.claim_type | titlecase }}</p>
              <p><strong>Lecteur :</strong> {{ assignedUser() || 'Inconnu' }}</p>
            </div>
            <div class="claim-metrics">
              <p><strong>Indice de complétude</strong></p>
              <p class="metric-value">{{ (claim()?.completeness_score != null) ? (claim()!.completeness_score | number:'1.0-0') + '%' : 'N/A' }}</p>
              <div class="progress-bar">
                <div class="progress-fill" [style.width.%]="claim()?.completeness_score || 0"></div>
              </div>
            </div>
          </div>
          <div *ngIf="missingRequiredDocuments.length" class="missing-required">
            <p class="missing-label">Documents obligatoires manquants :</p>
            <ul>
              <li *ngFor="let doc of missingRequiredDocuments">{{ doc | titlecase }}</li>
            </ul>
          </div>
          <div *ngIf="!missingRequiredDocuments.length" class="missing-required complete">
            Tous les documents obligatoires sont présents pour ce type de sinistre.
          </div>

          <form [formGroup]="uploadForm" (ngSubmit)="uploadDocument()" class="upload-form">
            <div class="field-row">
              <label for="file">Choisir un document</label>
              <input id="file" type="file" formControlName="file" (change)="onFileChange($event)" />
              <small *ngIf="fileError()" class="error">{{ fileError() }}</small>
            </div>
            <button class="primary-btn" type="submit" [disabled]="uploadForm.invalid || uploading() || !selectedFile">
              Téléverser
            </button>
          </form>

          <div class="message" [class.error]="errorMessage()" [class.success]="successMessage()">
            <span *ngIf="errorMessage()">{{ errorMessage() }}</span>
            <span *ngIf="successMessage()">{{ successMessage() }}</span>
          </div>

          <div class="documents-panel">
            <h2>Documents téléversés</h2>
            <div *ngIf="documents().length; else noDocs">
              <ul class="item-list">
                <li *ngFor="let document of documents()">
                  <div>
                    <strong>{{ document.file_name }}</strong>
                    <small>Type : {{ document.document_type || 'Non classé' }}</small>
                  </div>
                  <div class="item-actions">
                    <span *ngIf="document.classification_confidence !== undefined" class="confidence-badge" [ngClass]="getConfidenceClass(document.classification_confidence)">
                      {{ (document.classification_confidence * 100) | number:'1.0-0' }}%
                    </span>
                    <button class="link-btn" (click)="navigateToDocument(document.id)">Voir</button>
                  </div>
                </li>
              </ul>
            </div>
            <ng-template #noDocs>
              <p class="empty-state">Aucun document téléversé pour ce sinistre.</p>
            </ng-template>
          </div>
        </div>
      </section>

      <ng-template #loading>
        <p class="loading-text">Chargement des détails du sinistre...</p>
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
        gap: 1rem;
        align-items: center;
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
        font-size: clamp(2rem, 2.5vw, 2.75rem);
        line-height: 1.05;
        color: #0f172a;
      }
      .lead {
        margin: 0.75rem 0 0;
        color: #475569;
      }
      .ghost-btn,
      .primary-btn {
        border: none;
        border-radius: 16px;
        cursor: pointer;
        padding: 1rem 1.25rem;
        font-weight: 700;
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
      .claim-summary {
        display: grid;
        grid-template-columns: minmax(0, 1.4fr) minmax(280px, 1fr);
        gap: 1.5rem;
        margin-bottom: 1.5rem;
        padding: 1.5rem;
        border-radius: 24px;
        background: #f8fafc;
      }
      .claim-info {
        display: grid;
        gap: 0.75rem;
      }
      .claim-metrics {
        min-width: 220px;
        display: grid;
        gap: 0.75rem;
        align-items: start;
      }
      .metric-value {
        margin: 0;
        font-size: 1.85rem;
        color: #0f172a;
        font-weight: 700;
      }
      .progress-bar {
        width: 100%;
        height: 0.75rem;
        border-radius: 999px;
        background: #e2e8f0;
        overflow: hidden;
      }
      .progress-fill {
        height: 100%;
        background: linear-gradient(135deg, #2563eb, #9333ea);
        border-radius: 999px;
      }
      .missing-required {
        margin-top: 1rem;
        padding: 1rem;
        border-radius: 20px;
        background: #f8fafc;
        color: #334155;
      }
      .missing-required.complete {
        background: #ecfdf5;
        color: #166534;
      }
      .missing-required ul {
        margin: 0.75rem 0 0;
        padding-left: 1.25rem;
      }
      .missing-label {
        margin: 0;
        font-weight: 700;
      }
      .upload-form {
        display: grid;
        gap: 1rem;
        margin-bottom: 1.25rem;
      }
      .field-row {
        display: grid;
        gap: 0.5rem;
      }
      label {
        font-weight: 700;
        color: #0f172a;
      }
      input[type="file"] {
        width: 100%;
      }
      .item-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 1rem;
      }
      li {
        display: grid;
        grid-template-columns: 1fr auto;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        border-radius: 20px;
        background: #f8fafc;
      }
      .empty-state,
      .loading-text {
        color: #64748b;
      }
      .message {
        min-height: 1.25rem;
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
      .item-actions {
        display: flex;
        align-items: center;
        gap: 0.75rem;
      }
      .link-btn {
        border: none;
        background: transparent;
        color: #2563eb;
        font-weight: 700;
        cursor: pointer;
      }
    `
  ]
})
export class ClaimDetailComponent {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private fb = inject(FormBuilder);

  claim = signal<Claim | null>(null);
  documents = signal<DocumentItem[]>([]);
  selectedFile: File | null = null;
  uploading = signal(false);
  errorMessage = signal('');
  successMessage = signal('');
  assignedUser = signal('');
  fileError = signal('');

  requiredDocuments = {
    auto: ['declaration_sinistre', 'carte_grise', 'permis_conduire', 'constat_amiable'],
    habitation: ['declaration_sinistre', 'devis'],
    sante: ['declaration_sinistre', 'facture'],
  } as const;

  uploadForm = this.fb.group({
    file: this.fb.control<File | null>(null, Validators.required),
  });

  constructor() {
    if (!this.auth.isAuthenticated) {
      this.router.navigate(['/']);
      return;
    }
    const claimId = Number(this.route.snapshot.paramMap.get('id'));
    if (claimId) {
      this.loadClaim(claimId);
      this.loadDocuments(claimId);
    } else {
      this.router.navigate(['/claims']);
    }
  }

  get missingRequiredDocuments() {
    const claim = this.claim();
    if (!claim) {
      return [];
    }
    const required = this.requiredDocuments[claim.claim_type as keyof typeof this.requiredDocuments] ?? [];
    const presentTypes = new Set(this.documents().map((doc) => doc.document_type).filter(Boolean));
    return required.filter((docType) => !presentTypes.has(docType));
  }

  loadUserName(userId: number) {
    this.http.get<User>(`http://localhost:8000/users/${userId}`, this.auth.authOptions).subscribe({
      next: (user) => this.assignedUser.set(user.name),
      error: () => this.assignedUser.set(`User ${userId}`),
    });
  }

  loadClaim(claimId: number) {
    this.http.get<Claim>(`http://localhost:8000/claims/${claimId}`, this.auth.authOptions).subscribe({
      next: (claim) => {
        this.claim.set(claim);
        if (claim.user_id) {
          this.loadUserName(claim.user_id);
        } else {
          this.assignedUser.set('Inconnu');
        }
      },
      error: () => {
        this.router.navigate(['/claims']);
      }
    });
  }

  loadDocuments(claimId: number) {
    this.http.get<DocumentItem[]>(`http://localhost:8000/documents?claim_id=${claimId}`, this.auth.authOptions).subscribe({
      next: (docs) => this.documents.set(docs),
      error: () => this.documents.set([]),
    });
  }

  getConfidenceClass(confidence: number | undefined): string {
    if (confidence === undefined || confidence === null) {
      return '';
    }
    if (confidence < 0.25) {
      return 'conf-low';
    }
    if (confidence < 0.45) {
      return 'conf-med';
    }
    return 'conf-high';
  }

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
    this.uploadForm.patchValue({ file: this.selectedFile });
    this.uploadForm.get('file')?.markAsTouched();
    this.fileError.set('');
    if (!this.selectedFile) {
      this.fileError.set('Please select a document file.');
    }
  }

  uploadDocument() {
    if (!this.selectedFile || !this.claim()) {
      this.fileError.set('Please select a file before uploading.');
      return;
    }

    const formData = new FormData();
    formData.append('claim_id', String(this.claim()?.id));
    formData.append('file', this.selectedFile);

    this.uploading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');

    this.http.post<DocumentItem>('http://localhost:8000/documents/upload', formData, {
      headers: this.auth.authHeaders,
    }).subscribe({
      next: () => {
        this.successMessage.set('Document téléversé et classé avec succès.');
        this.uploading.set(false);
        this.selectedFile = null;
        this.uploadForm.reset();
        const currentClaim = this.claim();
        if (currentClaim) {
          this.loadDocuments(currentClaim.id);
          this.loadClaim(currentClaim.id);
        }
      },
      error: () => {
        this.errorMessage.set('Échec du téléversement. Veuillez réessayer.');
        this.uploading.set(false);
      }
    });
  }

  navigateBack() {
    this.router.navigate(['/claims']);
  }

  navigateToDocument(documentId: number) {
    this.router.navigate(['/documents', documentId]);
  }
}
