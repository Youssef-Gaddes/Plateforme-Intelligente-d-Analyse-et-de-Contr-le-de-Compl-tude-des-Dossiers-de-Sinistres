import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { AuthService } from './auth.service';

interface DocumentDetail {
  id: number;
  claim_id: number;
  file_name: string;
  document_type?: string;
  classification_confidence?: number;
  is_manually_reviewed?: boolean;
  ocr_text?: string;
}

@Component({
  standalone: true,
  selector: 'app-document-detail',
  imports: [CommonModule],
  template: `
    <div class="page-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">Document details</p>
          <h1>{{ document()?.file_name || 'Loading document...' }}</h1>
          <p class="lead">Review file metadata, predicted type, and OCR text for this document.</p>
        </div>
        <button class="ghost-btn" (click)="navigateBack()">Back to dashboard</button>
      </header>

      <section class="panel">
        <div *ngIf="document(); else loading">
          <div class="detail-grid">
            <div class="detail-row">
              <strong>Claim ID</strong>
              <span>{{ document()?.claim_id }}</span>
            </div>
            <div class="detail-row">
              <strong>Document type</strong>
              <span>{{ document()?.document_type || 'Unclassified' }}</span>
            </div>
            <div class="detail-row">
              <strong>Confidence</strong>
              <span [ngClass]="getConfidenceClass(document()?.classification_confidence)" class="confidence-badge">
                {{ document()?.classification_confidence != null ? ((document()?.classification_confidence! * 100) | number:'1.0-0') + '%' : 'N/A' }}
              </span>
            </div>
            <div class="detail-row flagged" *ngIf="isReviewFlagged()">
              <strong>Review status</strong>
              <span>Low confidence document flagged for manual review.</span>
            </div>
            <div class="detail-row reviewed" *ngIf="document()?.is_manually_reviewed">
              <strong>Review status</strong>
              <span>Document manually reviewed.</span>
            </div>
            <div class="detail-row review-form" *ngIf="canReview()">
              <strong>Manual review</strong>
              <div class="review-controls">
                <select [value]="selectedType()" (change)="selectedType.set($any($event.target).value)">
                  <option *ngFor="let type of types()" [value]="type">{{ type }}</option>
                </select>
                <button class="primary-btn" type="button" [disabled]="saving() || !selectedType()" (click)="saveType()">
                  Save type
                </button>
              </div>
              <p class="helper-text">Only gestionnaire or admin may correct the predicted document type when confidence is low.</p>
              <p class="message success" *ngIf="message() && !isError">{{ message() }}</p>
              <p class="message error" *ngIf="message() && isError">{{ message() }}</p>
            </div>
            <div class="detail-row">
              <strong>OCR text</strong>
              <p class="ocr-text">{{ document()?.ocr_text || 'No OCR text available.' }}</p>
            </div>
            <div class="detail-row" *ngIf="fileUrl()">
              <strong>Preview</strong>
              <div class="file-preview">
                <ng-container [ngSwitch]="getPreviewType(document()?.file_name)">
                  <img *ngSwitchCase="'image'" [src]="fileUrl()" alt="Document preview" />
                  <iframe *ngSwitchCase="'pdf'" [src]="fileUrl()" title="Document preview"></iframe>
                  <a *ngSwitchDefault [href]="fileUrl()" target="_blank" rel="noopener">Open document</a>
                </ng-container>
              </div>
            </div>
          </div>
        </div>
      </section>

      <ng-template #loading>
        <p class="loading-text">Loading document details...</p>
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
        font-size: clamp(2rem, 2.5vw, 2.75rem);
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
      .detail-grid {
        display: grid;
        gap: 1rem;
      }
      .detail-row {
        display: grid;
        gap: 0.5rem;
        padding: 1rem;
        border-radius: 20px;
        background: #f8fafc;
      }

      .detail-row.flagged {
        border: 1px solid #facc15;
        background: #fefce8;
      }

      .review-controls {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }

      .review-controls select {
        min-width: 220px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        padding: 0.85rem 1rem;
        background: #ffffff;
      }

      .helper-text {
        margin: 0.75rem 0 0;
        color: #64748b;
      }

      .message {
        margin: 0.75rem 0 0;
        font-weight: 700;
      }

      .message.success {
        color: #16a34a;
      }

      .message.error {
        color: #dc2626;
      }

      .confidence-badge {
        display: inline-flex;
        align-items: center;
        min-width: 4.5rem;
        justify-content: center;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
      }

      .conf-low {
        background: #fee2e2;
        color: #b91c1c;
      }

      .conf-med {
        background: #fef3c7;
        color: #92400e;
      }

      .conf-high {
        background: #dcfce7;
        color: #15803d;
      }

      .detail-row strong {
        color: #0f172a;
      }
      .ocr-text {
        margin: 0;
        color: #475569;
        white-space: pre-wrap;
      }
      .file-preview {
        min-height: 320px;
        border-radius: 18px;
        overflow: hidden;
        background: #f8fafc;
      }
      .file-preview img,
      .file-preview iframe {
        width: 100%;
        height: 100%;
        border: 0;
      }
      .loading-text {
        color: #64748b;
      }
    `
  ]
})
export class DocumentDetailComponent {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  document = signal<DocumentDetail | null>(null);
  fileUrl = signal<string | null>(null);
  types = signal<string[]>([]);
  selectedType = signal<string>('');
  saving = signal(false);
  message = signal('');
  isError = false;
  private currentObjectUrl: string | null = null;

  constructor() {
    if (!this.auth.isAuthenticated) {
      this.router.navigate(['/']);
      return;
    }
    const documentId = Number(this.route.snapshot.paramMap.get('id'));
    if (!documentId) {
      this.router.navigate(['/dashboard']);
      return;
    }
    this.loadDocument(documentId);
    this.loadDocumentTypes();
    this.loadFileBlob(documentId);
  }

  loadDocumentTypes() {
    this.http.get<string[]>('http://localhost:8000/documents/types', this.auth.authOptions).subscribe({
      next: (types) => this.types.set(types),
      error: () => this.types.set([]),
    });
  }

  loadDocument(documentId: number) {
    this.http.get<DocumentDetail>(`http://localhost:8000/documents/${documentId}`, this.auth.authOptions).subscribe({
      next: (document) => {
        this.document.set(document);
        this.selectedType.set(document.document_type || '');
      },
      error: () => this.router.navigate(['/dashboard']),
    });
  }

  saveType() {
    const documentId = Number(this.route.snapshot.paramMap.get('id'));
    if (!documentId) {
      return;
    }
    this.saving.set(true);
    this.message.set('');
    this.isError = false;

    this.http.put<DocumentDetail>(`http://localhost:8000/documents/${documentId}`, { document_type: this.selectedType() }, this.auth.authOptions).subscribe({
      next: (document) => {
        this.document.set(document);
        this.saving.set(false);
        this.message.set('Document type updated successfully.');
      },
      error: () => {
        this.saving.set(false);
        this.isError = true;
        this.message.set('Unable to update document type.');
      },
    });
  }

  canReview() {
    const confidence = this.document()?.classification_confidence;
    return (
      !this.document()?.is_manually_reviewed &&
      (this.auth.role() === 'gestionnaire' || this.auth.role() === 'admin') &&
      confidence !== undefined &&
      confidence < 0.3
    );
  }

  isReviewFlagged() {
    const confidence = this.document()?.classification_confidence;
    return !this.document()?.is_manually_reviewed && confidence !== undefined && confidence < 0.3;
  }

  getConfidenceClass(confidence: number | undefined | null): string {
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

  loadFileBlob(documentId: number) {
    if (!this.auth.authOptions) {
      return;
    }

    this.http.get(`http://localhost:8000/documents/${documentId}/file`, {
      ...this.auth.authOptions,
      responseType: 'blob',
    }).subscribe({
      next: (blob) => {
        if (this.currentObjectUrl) {
          URL.revokeObjectURL(this.currentObjectUrl);
        }
        this.currentObjectUrl = URL.createObjectURL(blob);
        this.fileUrl.set(this.currentObjectUrl);
      },
      error: () => {
        this.fileUrl.set(null);
      },
    });
  }

  getPreviewType(fileName: string | undefined | null) {
    if (!fileName) {
      return 'other';
    }
    const extension = fileName.split('.').pop()?.toLowerCase();
    if (extension === 'pdf') {
      return 'pdf';
    }
    if (extension === 'png' || extension === 'jpg' || extension === 'jpeg') {
      return 'image';
    }
    return 'other';
  }

  navigateBack() {
    this.router.navigate(['/dashboard']);
  }
}
