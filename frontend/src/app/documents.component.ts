import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

interface DocumentItem {
  id: number;
  claim_id: number;
  file_name: string;
  document_type?: string;
  classification_confidence?: number;
  is_manually_reviewed?: boolean;
}

@Component({
  standalone: true,
  selector: 'app-documents',
  imports: [CommonModule],
  template: `
    <div class="page-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">Documents</p>
          <h1>Document library</h1>
          <p class="lead">Browse uploaded documents and manage them with one click.</p>
        </div>
        <button class="ghost-btn" (click)="navigateHome()">Back to dashboard</button>
      </header>

      <section class="panel">
        <div class="panel-header">
          <h2>All documents</h2>
          <span class="badge">{{ displayedDocuments().length }}</span>
        </div>
        <div class="list-controls">
          <label>
            Sort by
            <select (change)="setSortField($event)">
              <option value="file_name">File name</option>
              <option value="claim_id">Claim ID</option>
              <option value="document_type">Type</option>
              <option value="classification_confidence">Confidence</option>
            </select>
          </label>
          <button class="ghost-btn" type="button" (click)="toggleSortOrder()">
            {{ sortOrder() === 'asc' ? 'Ascending' : 'Descending' }}
          </button>
        </div>
        <div *ngIf="displayedDocuments().length; else noDocs">
          <ul class="item-list">
                        <li *ngFor="let document of displayedDocuments()">
              <div>
                <strong>{{ document.file_name }}</strong>
                <small>
                  Claim {{ document.claim_id }} · {{ document.document_type || 'Unclassified' }}
                  <span *ngIf="document.classification_confidence != null" class="confidence-badge" [ngClass]="getConfidenceClass(document.classification_confidence)">
                    Confidence: {{ (document.classification_confidence * 100) | number:'1.0-0' }}%
                  </span>
                  <span *ngIf="document.is_manually_reviewed" class="confidence-badge conf-high">
                    Reviewed manually
                  </span>
                </small>
              </div>
              <div class="item-actions">
                <button class="link-btn" (click)="navigateToDocument(document.id)">View</button>
                <button class="link-btn" *ngIf="isAdmin" (click)="deleteDocument(document.id)">Delete</button>
              </div>
            </li>
          </ul>
        </div>
        <ng-template #noDocs>
          <p class="empty-state">No documents uploaded yet.</p>
        </ng-template>
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
      .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
      }
      .badge {
        background: rgba(37, 99, 235, 0.12);
        color: #2563eb;
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        font-weight: 700;
      }
      .item-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: grid;
        gap: 1rem;
        
      }
      li {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        border-radius: 20px;
        background: #f8fafc;
      }
      li strong {
        display: block;
        font-size: 1rem;
        color: #0f172a;
      }
      li small {
        display: block;
        color: #64748b;
      }
      .item-actions {
        display: flex;
        gap: 0.75rem;
      }
      .link-btn {
        border: none;
        background: transparent;
        color: #2563eb;
        cursor: pointer;
        font-weight: 700;
      }
            .confidence-badge {
        display: inline-block;
        margin-left: 0.5rem;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        vertical-align: middle;
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
      .empty-state {
        margin: 0;
        color: #64748b;
      }
    `
  ]
})
export class DocumentsComponent {
  private http = inject(HttpClient);
  private router = inject(Router);
  private auth = inject(AuthService);

  documents = signal<DocumentItem[]>([]);
  sortField = signal<'file_name' | 'claim_id' | 'document_type' | 'classification_confidence'>('file_name');
  sortOrder = signal<'asc' | 'desc'>('asc');

  get displayedDocuments() {
    return () => {
      return [...this.documents()].sort((a, b) => {
        const field = this.sortField();
        const dir = this.sortOrder() === 'asc' ? 1 : -1;
        const left = a[field] ?? '';
        const right = b[field] ?? '';
        if (left < right) {
          return -1 * dir;
        }
        if (left > right) {
          return 1 * dir;
        }
        return 0;
      });
    };
  }

  setSortField(event: Event) {
    const value = (event.target as HTMLSelectElement).value as 'file_name' | 'claim_id' | 'document_type' | 'classification_confidence';
    this.sortField.set(value);
  }

  toggleSortOrder() {
    this.sortOrder.set(this.sortOrder() === 'asc' ? 'desc' : 'asc');
  }

  get isAdmin() {
    return this.auth.role() === 'admin';
  }

    getConfidenceClass(confidence: number | undefined): string {
    if (confidence === undefined || confidence === null) return '';
    if (confidence < 0.25) return 'conf-low';
    if (confidence < 0.45) return 'conf-med';
    return 'conf-high';
  }

  constructor() {
    if (!this.auth.isAuthenticated) {
      this.router.navigate(['/']);
      return;
    }
    this.loadDocuments();
  }

  loadDocuments() {
    this.http.get<DocumentItem[]>('http://localhost:8000/documents', this.auth.authOptions).subscribe({
      next: (docs) => this.documents.set(docs),
      error: () => this.documents.set([]),
    });
  }

  navigateHome() {
    this.router.navigate(['/dashboard']);
  }

  navigateToDocument(documentId: number) {
    this.router.navigate(['/documents', documentId]);
  }

  deleteDocument(documentId: number) {
    if (!confirm('Delete this document permanently?')) {
      return;
    }

    this.http.delete(`http://localhost:8000/documents/${documentId}`, this.auth.authOptions).subscribe({
      next: () => this.loadDocuments(),
      error: () => alert('Unable to delete document.'),
    });
  }
}
