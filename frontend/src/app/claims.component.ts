import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
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
  user_id?: number;
}

@Component({
  standalone: true,
  selector: 'app-claims',
  imports: [CommonModule],
  template: `
    <div class="page-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">Sinistres</p>
          <h1>{{ headerTitle() }}</h1>
          <p class="lead">{{ headerSubtitle() }}</p>
        </div>
        <div class="header-actions">
          <button class="ghost-btn" (click)="navigateHome()">Retour au tableau de bord</button>
          <button class="primary-btn" *ngIf="canCreate()" (click)="navigateToNew()">Créer un sinistre</button>
        </div>
      </header>

      <section class="panel" *ngIf="isGestionnaire">
        <div class="panel-header">
          <h2>Recherche de lecteur</h2>
          <span class="badge">{{ users().length }} lecteurs</span>
        </div>
        <div class="search-row">
          <input
            type="search"
            placeholder="Rechercher un lecteur par nom ou email"
            (input)="setSearchTerm($event)"
          />
        </div>

        <div *ngIf="searchTerm().length >= 2; else searchPrompt">
          <div *ngIf="matchingUsers().length; else noUserMatches">
            <ul class="item-list">
              <li *ngFor="let user of matchingUsers()" [class.selected]="selectedUser()?.id === user.id" (click)="selectUser(user)">
                <div>
                  <strong>{{ user.name }}</strong>
                  <small>{{ user.email }}</small>
                </div>
                <span class="role-pill">lecteur</span>
              </li>
            </ul>
          </div>
        </div>

        <ng-template #noUserMatches>
          <p class="empty-state">Aucun lecteur correspondant trouvé.</p>
        </ng-template>

        <ng-template #searchPrompt>
          <p class="empty-state">Tapez au moins deux caractères pour rechercher un lecteur.</p>
        </ng-template>
      </section>

      <section class="panel">
        <div class="panel-header">
          <h2>{{ listTitle() }}</h2>
          <span class="badge">{{ displayedClaims().length }}</span>
        </div>

        <div class="list-controls">
          <label>
            Trier par
            <select (change)="setSortField($event)">
              <option value="claim_number">Numéro</option>
              <option value="insured_name">Assuré</option>
              <option value="status">Statut</option>
              <option value="claim_type">Type</option>
              <option value="completeness_score">Complétude</option>
              <option value="user_id">Lecteur</option>
            </select>
          </label>
          <button class="ghost-btn" type="button" (click)="toggleSortOrder()">
            {{ sortOrder() === 'asc' ? 'Ascendant' : 'Descendant' }}
          </button>
        </div>

        <div *ngIf="displayedClaims().length; else noClaims">
          <ul class="item-list">
            <li *ngFor="let claim of displayedClaims()">
              <div>
                <strong>{{ claim.claim_number }}</strong>
                <small>{{ claim.insured_name }}</small>
                <div class="claim-meta">
                  <span class="badge type-badge">{{ claim.claim_type | titlecase }}</span>
                  <span [class]="'badge status-badge status-' + claim.status">{{ claim.status | titlecase }}</span>
                  <span class="badge completeness-badge" *ngIf="claim.completeness_score != null">{{ claim.completeness_score | number:'1.0-0' }}%</span>
                  <span class="badge reader-badge" *ngIf="claim.user_id != null && !isLecteur">Lecteur {{ claim.user_id }}</span>
                </div>
              </div>
              <div class="item-actions">
                <button class="link-btn" (click)="navigateToClaim(claim.id)">Voir</button>
                <button class="link-btn" *ngIf="canEdit()" (click)="navigateToEdit(claim.id)">Modifier</button>
                <button class="link-btn danger" *ngIf="isAdmin" (click)="deleteClaim(claim.id)">Supprimer</button>
              </div>
            </li>
          </ul>
        </div>

        <ng-template #noClaims>
          <p class="empty-state">Aucun sinistre disponible pour l’utilisateur sélectionné.</p>
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
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        padding: 1.75rem 2rem;
        border-radius: 28px;
        background: #ffffff;
        box-shadow: 0 30px 70px rgba(15, 23, 42, 0.08);
      }
      .header-actions {
        display: flex;
        gap: 0.75rem;
        flex-wrap: wrap;
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
        min-height: 3rem;
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
      .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
      }
      .panel-header h2 {
        margin: 0;
        font-size: 1.125rem;
      }
      .badge {
        background: rgba(37, 99, 235, 0.12);
        color: #2563eb;
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        font-weight: 700;
      }
      .search-row {
        margin-top: 1rem;
      }
      .search-row input {
        width: 100%;
        min-height: 3rem;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        padding: 0.95rem 1rem;
        font: inherit;
        background: #f8fafc;
      }
      .selected-user-banner {
        margin-top: 1rem;
        padding: 1rem 1.25rem;
        border-radius: 20px;
        background: #eef2ff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
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
      li {
        cursor: default;
      }
      .claim-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0.75rem 0 0;
      }
      .claim-meta .badge {
        color: #102a43;
        background: #e2e8f0;
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 700;
      }
      .claim-meta .type-badge {
        background: #eff6ff;
        color: #1d4ed8;
      }
      .claim-meta .status-badge {
        background: #f8fafc;
        color: #334155;
      }
      .claim-meta .status-badge.status-ouvert {
        background: #eff6ff;
        color: #1d4ed8;
      }
      .claim-meta .status-badge.status-en_cours {
        background: #fffbeb;
        color: #92400e;
      }
      .claim-meta .status-badge.status-ferme {
        background: #f0fdf4;
        color: #166534;
      }
      .claim-meta .completeness-badge {
        background: #ecfdfa;
        color: #166534;
      }
      .claim-meta .reader-badge {
        background: #eef2ff;
        color: #1d4ed8;
      }
      li.selected {
        border: 1px solid #2563eb;
      }
      li div {
        min-width: 0;
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
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
      }
      .link-btn {
        border: none;
        background: transparent;
        color: #2563eb;
        font-weight: 700;
        cursor: pointer;
      }
      .link-btn.danger {
        color: #dc2626;
      }
      .status-pill,
      .role-pill {
        padding: 0.45rem 0.85rem;
        border-radius: 999px;
        font-weight: 700;
      }

      .list-controls {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        margin-bottom: 1rem;
      }

      .list-controls label {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #475569;
        font-weight: 600;
      }

      .list-controls select {
        min-width: 180px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        padding: 0.75rem 1rem;
        background: #ffffff;
        color: #0f172a;
      }
      .status-pill {
        background: #e2e8f0;
        color: #0f172a;
      }
      .role-pill {
        background: #eef2ff;
        color: #2563eb;
      }
      .empty-state {
        margin: 0;
        color: #64748b;
      }
      @media (max-width: 720px) {
        .page-shell,
        .panel {
          padding: 1rem;
        }
        .page-header {
          padding: 1.25rem;
        }
        .item-actions {
          justify-content: flex-end;
        }
      }
    `
  ]
})
export class ClaimsComponent {
  private http = inject(HttpClient);
  private router = inject(Router);
  private auth = inject(AuthService);

  claims = signal<Claim[]>([]);
  users = signal<User[]>([]);
  selectedUser = signal<User | null>(null);
  searchTerm = signal('');
  sortField = signal<'claim_number' | 'insured_name' | 'status' | 'user_id' | 'claim_type' | 'completeness_score'>('claim_number');
  sortOrder = signal<'asc' | 'desc'>('asc');

  constructor() {
    if (!this.auth.isAuthenticated) {
      this.router.navigate(['/']);
      return;
    }
    this.loadClaims();
    if (this.isGestionnaire) {
      this.loadLecteurs();
    }
  }

  get role() {
    return this.auth.role();
  }

  get isAdmin() {
    return this.role === 'admin';
  }

  get isGestionnaire() {
    return this.role === 'gestionnaire';
  }

  get isLecteur() {
    return this.role === 'lecteur';
  }

  get matchingUsers() {
    return () => {
      const term = this.searchTerm().toLowerCase().trim();
      return this.users().filter((user) => user.name.toLowerCase().includes(term) || user.email.toLowerCase().includes(term));
    };
  }

  get displayedClaims() {
    return () => {
      const filtered = this.isGestionnaire && this.selectedUser()
        ? this.claims().filter((claim) => claim.user_id === this.selectedUser()!.id)
        : this.claims();

      return [...filtered].sort((a, b) => {
        const field = this.sortField();
        const dir = this.sortOrder() === 'asc' ? 1 : -1;
        const left = a[field] ?? '';
        const right = b[field] ?? '';
        if (typeof left === 'number' && typeof right === 'number') {
          return (left - right) * dir;
        }
        const leftStr = String(left).toLowerCase();
        const rightStr = String(right).toLowerCase();
        if (leftStr < rightStr) {
          return -1 * dir;
        }
        if (leftStr > rightStr) {
          return 1 * dir;
        }
        return 0;
      });
    };
  }

  setSortField(event: Event) {
    const value = (event.target as HTMLSelectElement).value as 'claim_number' | 'insured_name' | 'status' | 'user_id' | 'claim_type' | 'completeness_score';
    this.sortField.set(value);
  }

  toggleSortOrder() {
    this.sortOrder.set(this.sortOrder() === 'asc' ? 'desc' : 'asc');
  }

  headerTitle() {
    if (this.isGestionnaire) {
      return 'Gérer les sinistres des lecteurs';
    }
    if (this.isLecteur) {
      return 'Vos sinistres';
    }
    return 'Tous les sinistres';
  }

  headerSubtitle() {
    if (this.isGestionnaire) {
      return 'Recherchez un lecteur et gérez ses sinistres. Création et modification possibles, suppression réservée à l’admin.';
    }
    if (this.isLecteur) {
      return 'Consultez vos sinistres et téléversez des documents associés.';
    }
    return 'Parcourez tous les sinistres, créez-en de nouveaux et gérez-les avec les permissions administrateur.';
  }

  listTitle() {
    if (this.isGestionnaire) {
      return this.selectedUser() ? 'Sinistres du lecteur sélectionné' : 'Recherchez un lecteur pour afficher ses sinistres';
    }
    if (this.isLecteur) {
      return 'Vos sinistres';
    }
    return 'Liste des sinistres';
  }

  canCreate() {
    return this.isAdmin || this.isGestionnaire;
  }

  canEdit() {
    return this.isAdmin || this.isGestionnaire;
  }

  loadClaims() {
    this.http.get<Claim[]>('http://localhost:8000/claims', this.auth.authOptions).subscribe({
      next: (claims) => this.claims.set(claims),
      error: () => this.claims.set([]),
    });
  }

  loadLecteurs() {
    this.http.get<User[]>('http://localhost:8000/users?role=lecteur', this.auth.authOptions).subscribe({
      next: (users) => this.users.set(users),
      error: () => this.users.set([]),
    });
  }

  setSearchTerm(event: Event) {
    const target = event.target as HTMLInputElement;
    this.searchTerm.set(target.value);
  }

  selectUser(user: User) {
    this.selectedUser.set(user);
  }

  clearSelectedUser() {
    this.selectedUser.set(null);
    this.searchTerm.set('');
  }

  navigateToClaim(claimId: number) {
    this.router.navigate(['/claims', claimId]);
  }

  navigateToEdit(claimId: number) {
    this.router.navigate(['/claims', claimId, 'edit']);
  }

  navigateToNew() {
    this.router.navigate(['/claims/new']);
  }

  deleteClaim(claimId: number) {
    if (!confirm('Supprimer définitivement ce sinistre ?')) {
      return;
    }
    this.http.delete(`http://localhost:8000/claims/${claimId}`, this.auth.authOptions).subscribe({
      next: () => this.loadClaims(),
      error: () => alert('Unable to delete claim.'),
    });
  }

  navigateHome() {
    this.router.navigate(['/dashboard']);
  }
}
