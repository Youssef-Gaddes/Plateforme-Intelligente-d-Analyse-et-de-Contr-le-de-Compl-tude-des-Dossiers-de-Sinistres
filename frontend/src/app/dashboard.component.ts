import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

interface Claim {
  id: number;
  claim_number: string;
  insured_name: string;
  status: string;
  claim_type: string;
  completeness_score?: number | null;
  user_id?: number | null;
}

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
  selector: 'app-dashboard',
  imports: [CommonModule],
  template: `
    <div class="dashboard-shell">

      <!-- Welcome Header -->
      <header class="welcome-header">
        <div class="welcome-text">
          <p class="eyebrow">Tableau de bord</p>
          <h1>Bonjour, <span class="highlight">{{ userLabel }}</span> 👋</h1>
          <p class="lead">Voici un aperçu de l'activité de votre plateforme de gestion des sinistres.</p>
        </div>
        <div class="header-actions">
          <button class="primary-btn" (click)="router.navigate(['/claims/new'])" *ngIf="canCreate">
            + Nouveau sinistre
          </button>
        </div>
      </header>

      <!-- KPI Cards -->
      <section class="kpi-grid" *ngIf="!loading()">
        <div class="kpi-card kpi-blue">
          <div class="kpi-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="kpi-body">
            <p class="kpi-value">{{ totalClaims() }}</p>
            <p class="kpi-label">Sinistres totaux</p>
          </div>
        </div>

        <div class="kpi-card kpi-amber">
          <div class="kpi-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div class="kpi-body">
            <p class="kpi-value">{{ openClaims() }}</p>
            <p class="kpi-label">Sinistres ouverts</p>
          </div>
        </div>

        <div class="kpi-card kpi-purple">
          <div class="kpi-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <div class="kpi-body">
            <p class="kpi-value">{{ totalDocuments() }}</p>
            <p class="kpi-label">Documents chargés</p>
          </div>
        </div>

        <div class="kpi-card kpi-green">
          <div class="kpi-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
          </div>
          <div class="kpi-body">
            <p class="kpi-value">{{ avgCompleteness() }}%</p>
            <p class="kpi-label">Complétude moyenne</p>
          </div>
        </div>
      </section>

      <!-- Loading skeleton -->
      <section class="kpi-grid" *ngIf="loading()">
        <div class="kpi-card skeleton" *ngFor="let i of [1,2,3,4]"></div>
      </section>

      <!-- Two-column: claim type breakdown + recent claims -->
      <section class="two-col" *ngIf="!loading()">

        <!-- Claim type breakdown -->
        <div class="panel">
          <div class="panel-header">
            <h2>Répartition par type</h2>
          </div>
          <div class="type-breakdown">
            <div class="type-row" *ngFor="let t of claimTypes">
              <div class="type-info">
                <span class="type-dot" [class]="'dot-' + t.key"></span>
                <span class="type-name">{{ t.label }}</span>
              </div>
              <div class="type-bar-wrap">
                <div class="type-bar" [class]="'bar-' + t.key" [style.width.%]="typePercent(t.key)"></div>
              </div>
              <span class="type-count">{{ typeCount(t.key) }}</span>
            </div>
          </div>
        </div>

        <!-- Recent claims -->
        <div class="panel">
          <div class="panel-header">
            <h2>Sinistres récents</h2>
            <button class="link-btn" (click)="router.navigate(['/claims'])">Voir tout →</button>
          </div>
          <ul class="recent-list" *ngIf="recentClaims().length; else noClaims">
            <li *ngFor="let claim of recentClaims()" (click)="router.navigate(['/claims', claim.id])">
              <div class="recent-info">
                <strong>{{ claim.claim_number }}</strong>
                <small>{{ claim.insured_name }}</small>
              </div>
              <div class="recent-meta">
                <span [class]="'status-chip status-' + claim.status">{{ claim.status | titlecase }}</span>
                <span class="score-chip" *ngIf="claim.completeness_score != null">
                  {{ claim.completeness_score | number:'1.0-0' }}%
                </span>
              </div>
            </li>
          </ul>
          <ng-template #noClaims>
            <p class="empty-state">Aucun sinistre pour le moment.</p>
          </ng-template>
        </div>

      </section>

      <!-- Document type breakdown -->
      <section class="panel doc-types-panel" *ngIf="!loading()">
        <div class="panel-header">
          <h2>Types de documents</h2>
        </div>

        <div class="donut-row" *ngIf="documentTypeSegments().length; else noDocs">
          <svg viewBox="0 0 160 160" class="donut-chart">
            <circle cx="80" cy="80" r="70" fill="none" stroke="#f1f5f9" stroke-width="20" />
            <circle *ngFor="let seg of documentTypeSegments()"
                   cx="80" cy="80" r="70" fill="none"
                   [attr.stroke]="seg.color"
                   stroke-width="20"
                   [attr.stroke-dasharray]="seg.dasharray"
                   [attr.stroke-dashoffset]="seg.dashoffset"
                   transform="rotate(-90 80 80)" />
           <text x="80" y="76" text-anchor="middle" class="donut-total">{{ totalDocuments() }}</text>
           <text x="80" y="94" text-anchor="middle" class="donut-total-label">documents</text>
         </svg>

         <ul class="doc-type-legend">
            <li *ngFor="let seg of documentTypeSegments()">
              <span class="legend-dot" [style.background]="seg.color"></span>
              <span class="legend-label">{{ seg.label }}</span>
              <span class="legend-count">{{ seg.count }}</span>
             <span class="legend-percent">{{ seg.percent | number:'1.0-0' }}%</span>
            </li>
          </ul>
        </div>

  <ng-template #noDocs>
    <p class="empty-state">Aucun document pour le moment.</p>
  </ng-template>
</section>

      <!-- Low-confidence alert panel -->
      <section class="panel alert-panel" *ngIf="!loading() && lowConfidenceDocs().length">
        <div class="panel-header">
          <h2>⚠ Documents à réviser</h2>
          <span class="badge badge-warning">{{ lowConfidenceDocs().length }}</span>
        </div>
        <p class="panel-desc">Ces documents ont une confiance de classification inférieure à 30% et nécessitent une révision manuelle.</p>
        <ul class="recent-list">
          <li *ngFor="let doc of lowConfidenceDocs()" (click)="router.navigate(['/documents', doc.id])">
            <div class="recent-info">
              <strong>{{ doc.file_name }}</strong>
              <small>Sinistre #{{ doc.claim_id }} · {{ doc.document_type || 'Non classé' }}</small>
            </div>
            <span class="confidence-chip" [ngClass]="getConfidenceClass(doc.classification_confidence)">
              {{ (doc.classification_confidence! * 100) | number:'1.0-0' }}%
            </span>
          </li>
        </ul>
      </section>

    </div>
  `,
  styles: [`
    :host {
      display: block;
      padding: 2rem;
    }

    .dashboard-shell {
      width: min(1200px, 100%);
      margin: 0 auto;
      display: grid;
      gap: 1.5rem;
    }

    /* ── Welcome Header ─────────────────────────── */
    .welcome-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
      padding: 2rem 2.25rem;
      border-radius: 28px;
      background: #ffffff;
      box-shadow: 0 20px 60px rgba(15, 23, 42, 0.07);
    }

    .eyebrow {
      margin: 0 0 0.4rem;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #2563eb;
    }

    h1 {
      margin: 0;
      font-size: clamp(1.75rem, 2.5vw, 2.25rem);
      font-weight: 800;
      color: #0f172a;
      line-height: 1.1;
    }

    .highlight {
      background: linear-gradient(135deg, #2563eb, #9333ea);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .lead {
      margin: 0.5rem 0 0;
      color: #64748b;
      font-size: 0.9375rem;
    }

    .primary-btn {
      padding: 0.875rem 1.5rem;
      border: none;
      border-radius: 16px;
      background: linear-gradient(135deg, #2563eb, #9333ea);
      color: #fff;
      font-weight: 700;
      font-size: 0.9375rem;
      cursor: pointer;
      white-space: nowrap;
      box-shadow: 0 8px 24px rgba(37, 99, 235, 0.25);
      transition: transform 0.15s, box-shadow 0.15s;
    }

    .primary-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 12px 32px rgba(37, 99, 235, 0.3);
    }

    /* ── KPI Cards ──────────────────────────────── */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
    }

    .kpi-card {
      display: flex;
      align-items: center;
      gap: 1.25rem;
      padding: 1.5rem;
      border-radius: 24px;
      background: #ffffff;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
      transition: transform 0.15s;
    }

    .kpi-card:hover { transform: translateY(-2px); }

    .kpi-icon {
      width: 52px;
      height: 52px;
      border-radius: 16px;
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .kpi-icon svg { width: 24px; height: 24px; }

    .kpi-blue .kpi-icon  { background: #eff6ff; color: #2563eb; }
    .kpi-amber .kpi-icon { background: #fffbeb; color: #d97706; }
    .kpi-purple .kpi-icon{ background: #f5f3ff; color: #7c3aed; }
    .kpi-green .kpi-icon { background: #f0fdf4; color: #16a34a; }

    .kpi-value {
      margin: 0;
      font-size: 2rem;
      font-weight: 800;
      color: #0f172a;
      line-height: 1;
    }

    .kpi-label {
      margin: 0.3rem 0 0;
      font-size: 0.8125rem;
      color: #64748b;
      font-weight: 500;
    }

    .doc-types-panel {
  padding: 1.5rem 2rem;
}

    .donut-row {
      display: flex;
      align-items: center;
      gap: 2.5rem;
      flex-wrap: wrap;
}

    .donut-chart {
      width: 160px;
      height: 160px;
      flex-shrink: 0;
}

    .donut-chart circle {
      transition: stroke-dasharray 0.4s ease;
}

    .donut-total {
      font-size: 1.5rem;
      font-weight: 800;
      fill: #0f172a;
}

    .donut-total-label {
      font-size: 0.7rem;
      fill: #64748b;
      font-weight: 500;
}

    .doc-type-legend {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 0.6rem;
      flex: 1;
      min-width: 220px;
}

    .doc-type-legend li {
      display: flex;
      align-items: center;
      gap: 0.6rem;
}

    .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
}

    .legend-label {
      font-size: 0.875rem;
      font-weight: 600;
      color: #334155;
      flex: 1;
}

    .legend-count {
      font-size: 0.8125rem;
      font-weight: 700;
      color: #0f172a;
}

    .legend-percent {
      font-size: 0.75rem;
      color: #94a3b8;
      font-weight: 600;
      width: 36px;
      text-align: right;
}

    @media (max-width: 600px) {
      .donut-row {
        flex-direction: column;
        align-items: flex-start;
      }
}

    .skeleton {
      height: 96px;
      background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
    }

    @keyframes shimmer {
      0%   { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }

    /* ── Two Column ─────────────────────────────── */
    .two-col {
      display: grid;
      grid-template-columns: 1fr 1.5fr;
      gap: 1rem;
    }

    /* ── Panel ──────────────────────────────────── */
    .panel {
      background: #ffffff;
      border-radius: 24px;
      padding: 1.5rem;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
    }

    .panel-header h2 {
      margin: 0;
      font-size: 1rem;
      font-weight: 700;
      color: #0f172a;
    }

    .panel-desc {
      margin: -0.5rem 0 1rem;
      font-size: 0.875rem;
      color: #64748b;
    }

    .link-btn {
      border: none;
      background: none;
      color: #2563eb;
      font-weight: 700;
      font-size: 0.875rem;
      cursor: pointer;
      padding: 0;
    }

    /* ── Claim Type Breakdown ───────────────────── */
    .type-breakdown {
      display: grid;
      gap: 1rem;
    }

    .type-row {
      display: grid;
      grid-template-columns: 140px 1fr 40px;
      align-items: center;
      gap: 0.75rem;
    }

    .type-info {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .type-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .dot-auto       { background: #2563eb; }
    .dot-habitation { background: #7c3aed; }
    .dot-sante      { background: #16a34a; }

    .type-name {
      font-size: 0.875rem;
      font-weight: 600;
      color: #334155;
      text-transform: capitalize;
    }

    .type-bar-wrap {
      height: 8px;
      border-radius: 999px;
      background: #f1f5f9;
      overflow: hidden;
    }

    .type-bar {
      height: 100%;
      border-radius: 999px;
      transition: width 0.4s ease;
    }

    .bar-auto       { background: #2563eb; }
    .bar-habitation { background: #7c3aed; }
    .bar-sante      { background: #16a34a; }

    .type-count {
      font-size: 0.875rem;
      font-weight: 700;
      color: #0f172a;
      text-align: right;
    }

    /* ── Recent Claims List ─────────────────────── */
    .recent-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 0.5rem;
    }

    .recent-list li {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      padding: 0.875rem 1rem;
      border-radius: 16px;
      background: #f8fafc;
      cursor: pointer;
      transition: background 0.15s;
    }

    .recent-list li:hover { background: #f1f5f9; }

    .recent-info strong {
      display: block;
      font-size: 0.9375rem;
      font-weight: 700;
      color: #0f172a;
    }

    .recent-info small {
      display: block;
      font-size: 0.8125rem;
      color: #64748b;
      margin-top: 0.15rem;
    }

    .recent-meta {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-shrink: 0;
    }

    /* Status chips */
    .status-chip {
      padding: 0.25rem 0.75rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
    }

    .status-ouvert   { background: #eff6ff; color: #1d4ed8; }
    .status-en_cours { background: #fffbeb; color: #92400e; }
    .status-ferme    { background: #f0fdf4; color: #166534; }

    .score-chip {
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
      background: #ecfdf5;
      color: #166534;
    }

    .confidence-chip {
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
      background: #fef3c7;
      color: #92400e;
      flex-shrink: 0;
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

    /* ── Alert Panel ────────────────────────────── */
    .alert-panel {
      border-left: 4px solid #f59e0b;
    }

    .badge {
      padding: 0.3rem 0.75rem;
      border-radius: 999px;
      font-weight: 700;
      font-size: 0.8rem;
    }

    .badge-warning {
      background: #fef3c7;
      color: #92400e;
    }

    .empty-state {
      margin: 0;
      color: #94a3b8;
      font-size: 0.9rem;
    }

    /* ── Responsive ─────────────────────────────── */
    @media (max-width: 1024px) {
      .kpi-grid { grid-template-columns: repeat(2, 1fr); }
      .two-col  { grid-template-columns: 1fr; }
    }

    @media (max-width: 600px) {
      :host { padding: 1rem; }
      .kpi-grid { grid-template-columns: 1fr; }
      .welcome-header { padding: 1.5rem; }
    }
  `]
})
export class DashboardComponent {
  private http = inject(HttpClient);
  protected router = inject(Router);
  private auth = inject(AuthService);

  claims = signal<Claim[]>([]);
  documents = signal<DocumentItem[]>([]);
  loading = signal(true);

  claimTypes = [
    { key: 'auto',       label: 'Auto' },
    { key: 'habitation', label: 'Habitation' },
    { key: 'sante',      label: 'Santé' },
  ];
  documentTypeMeta = [
  { key: 'declaration_sinistre', label: 'Déclaration de sinistre', color: '#2563eb' },
  { key: 'carte_grise',          label: 'Carte grise',              color: '#7c3aed' },
  { key: 'permis_conduire',      label: 'Permis de conduire',       color: '#16a34a' },
  { key: 'facture',              label: 'Facture',                  color: '#d97706' },
  { key: 'devis',                label: 'Devis',                    color: '#0891b2' },
  { key: 'constat_amiable',      label: 'Constat amiable',          color: '#e11d48' },
  { key: 'rapport_expertise',    label: "Rapport d'expertise",      color: '#4f46e5' },
  ];

  constructor() {
    if (!this.auth.isAuthenticated) {
      this.router.navigate(['/']);
      return;
    }
    this.loadData();
  }

  get userLabel() {
    const email = this.auth.email();
    return email ? email.split('@')[0] : this.auth.role() ?? 'utilisateur';
  }

  get canCreate() {
    return this.auth.role() === 'admin' || this.auth.role() === 'gestionnaire';
  }

  totalClaims = computed(() => this.claims().length);

  openClaims = computed(() =>
    this.claims().filter(c => c.status === 'ouvert').length
  );

  totalDocuments = computed(() => this.documents().length);

  documentTypeSegments = computed(() => {
  const docs = this.documents();
  const total = docs.length;
  if (!total) return [];

  const counts = new Map<string, number>();
  for (const doc of docs) {
    const key = doc.document_type ?? 'non_classe';
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const palette = [
    ...this.documentTypeMeta,
    { key: 'non_classe', label: 'Non classé', color: '#94a3b8' },
  ];

  const r = 70;
  const circumference = 2 * Math.PI * r;
  let cumulative = 0;

  return palette
    .map(meta => {
      const count = counts.get(meta.key) ?? 0;
      const percent = (count / total) * 100;
      const length = (percent / 100) * circumference;
      const segment = {
        ...meta,
        count,
        percent,
        dasharray: `${length} ${circumference - length}`,
        dashoffset: -cumulative,
      };
      cumulative += length;
      return segment;
    })
    .filter(s => s.count > 0);
  });

  avgCompleteness = computed(() => {
    const scored = this.claims().filter(c => c.completeness_score != null);
    if (!scored.length) return 0;
    const avg = scored.reduce((sum, c) => sum + c.completeness_score!, 0) / scored.length;
    return Math.round(avg);
  });

  recentClaims = computed(() => this.claims().slice(0, 5));

  typeCount(type: string) {
    return this.claims().filter(c => c.claim_type === type).length;
  }

  typePercent(type: string) {
    const total = this.claims().length;
    return total ? (this.typeCount(type) / total) * 100 : 0;
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

  lowConfidenceDocs = computed(() =>
    this.documents().filter(
      (d) => d.classification_confidence != null &&
             d.classification_confidence < 0.3 &&
             !d.is_manually_reviewed
    )
  );

  private loadData() {
    this.loading.set(true);
    let claimsLoaded = false;
    let docsLoaded = false;

    const checkDone = () => {
      if (claimsLoaded && docsLoaded) this.loading.set(false);
    };

    this.http.get<Claim[]>('http://localhost:8000/claims', this.auth.authOptions).subscribe({
      next: (c) => { this.claims.set(c); claimsLoaded = true; checkDone(); },
      error: () => { this.claims.set([]); claimsLoaded = true; checkDone(); },
    });

    this.http.get<DocumentItem[]>('http://localhost:8000/documents', this.auth.authOptions).subscribe({
      next: (d) => { this.documents.set(d); docsLoaded = true; checkDone(); },
      error: () => { this.documents.set([]); docsLoaded = true; checkDone(); },
    });
  }
}
