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
  role: 'admin' | 'gestionnaire' | 'lecteur';
}

@Component({
  standalone: true,
  selector: 'app-users',
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="page-shell">
      <header class="page-header">
        <div>
          <p class="eyebrow">User management</p>
          <h1>Manage users</h1>
          <p class="lead">Create, update, or delete users for your claims workflow.</p>
        </div>
        <button class="ghost-btn" (click)="navigateHome()">Back to dashboard</button>
      </header>

      <section class="admin-panel">
        <article class="panel">
          <div class="panel-header">
            <h2>Users</h2>
            <span class="badge">{{ displayedUsers().length }}</span>
          </div>

          <div class="list-controls">
            <label>
              Sort by
              <select (change)="setSortField($event)">
                <option value="name">Name</option>
                <option value="email">Email</option>
                <option value="role">Role</option>
              </select>
            </label>
            <button class="ghost-btn" type="button" (click)="toggleSortOrder()">
              {{ sortOrder() === 'asc' ? 'Ascending' : 'Descending' }}
            </button>
          </div>

          <div *ngIf="displayedUsers().length; else noUsers">
            <ul class="item-list">
              <li *ngFor="let user of displayedUsers()">
                <div>
                  <strong>{{ user.name }}</strong>
                  <small>{{ user.email }}</small>
                </div>
                <div class="item-actions">
                  <span class="role-pill">{{ user.role }}</span>
                  <button class="link-btn" type="button" (click)="editUser(user)">Edit</button>
                  <button class="link-btn danger" type="button" (click)="deleteUser(user.id)">Delete</button>
                </div>
              </li>
            </ul>
          </div>

          <ng-template #noUsers>
            <p class="empty-state">No users found. Add your first user.</p>
          </ng-template>
        </article>

        <article class="form-drawer">
          <div class="drawer-header">
            <div>
              <h2>{{ isEditing() ? 'Edit user' : 'Add user' }}</h2>
              <p class="lead">{{ isEditing() ? 'Update user details or reset password.' : 'Create a new user account for application access.' }}</p>
            </div>
            <button class="ghost-btn" type="button" (click)="resetForm()">
              {{ isEditing() ? 'New user' : 'Clear' }}
            </button>
          </div>

          <form [formGroup]="form" (ngSubmit)="saveUser()">
            <div class="field-row">
              <label for="name">Full name</label>
              <input id="name" formControlName="name" placeholder="Jean Dupont" />
              <small *ngIf="form.controls.name.invalid && form.controls.name.touched" class="error">Name is required.</small>
            </div>

            <div class="field-row">
              <label for="email">Email address</label>
              <input id="email" formControlName="email" placeholder="jean@exemple.com" />
              <small *ngIf="form.controls.email.invalid && form.controls.email.touched" class="error">Valid email is required.</small>
            </div>

            <div class="field-row">
              <label for="role">Role</label>
              <select id="role" formControlName="role">
                <option *ngFor="let role of roles" [value]="role">{{ role }}</option>
              </select>
            </div>

            <div class="field-row">
              <label for="password">{{ isEditing() ? 'New password (optional)' : 'Password' }}</label>
              <input id="password" type="password" formControlName="password" [placeholder]="isEditing() ? 'Leave blank to keep current password' : 'Enter password'" />
              <small *ngIf="!isEditing() && form.controls.password.invalid && form.controls.password.touched" class="error">Password is required for new users.</small>
            </div>

            <button class="primary-btn" type="submit" [disabled]="saving() || form.invalid || (!isEditing() && !form.controls.password.value)">
              {{ isEditing() ? 'Update user' : 'Create user' }}
            </button>

            <div class="message" [class.error]="errorMessage()" [class.success]="successMessage()">
              <span *ngIf="errorMessage()">{{ errorMessage() }}</span>
              <span *ngIf="successMessage()">{{ successMessage() }}</span>
            </div>
          </form>
        </article>
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

      .admin-panel {
        display: grid;
        gap: 1rem;
      }

      .panel,
      .form-drawer {
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
        padding: 1.1rem;
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

      .role-pill {
        background: #e0e7ff;
        color: #4338ca;
        border-radius: 999px;
        padding: 0.3rem 0.75rem;
        font-size: 0.85rem;
        font-weight: 700;
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

      .link-btn.danger {
        color: #dc2626;
      }

      .empty-state {
        margin: 0;
        color: #64748b;
      }

      .drawer-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
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

      @media (min-width: 950px) {
        .admin-panel {
          grid-template-columns: 1.5fr 1fr;
        }
      }

      @media (max-width: 720px) {
        :host {
          padding: 1rem;
        }

        .page-header,
        .panel,
        .form-drawer {
          padding: 1.25rem;
        }
      }
    `
  ]
})
export class UsersComponent {
  private http = inject(HttpClient);
  private router = inject(Router);
  private auth = inject(AuthService);
  private fb = inject(FormBuilder);

  users = signal<User[]>([]);
  selectedUser = signal<User | null>(null);
  isEditing = signal(false);
  saving = signal(false);
  errorMessage = signal('');
  successMessage = signal('');
  roles = ['admin', 'gestionnaire', 'lecteur'];
  sortField = signal<'name' | 'email' | 'role'>('name');
  sortOrder = signal<'asc' | 'desc'>('asc');

  form = this.fb.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    role: ['lecteur', Validators.required],
    password: [''],
  });

  constructor() {
    if (!this.auth.isAuthenticated || this.auth.role() !== 'admin') {
      this.router.navigate(['/dashboard']);
      return;
    }
    this.loadUsers();
  }

  get displayedUsers() {
    return () => {
      return [...this.users()].sort((a, b) => {
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
    const value = (event.target as HTMLSelectElement).value as 'name' | 'email' | 'role';
    this.sortField.set(value);
  }

  toggleSortOrder() {
    this.sortOrder.set(this.sortOrder() === 'asc' ? 'desc' : 'asc');
  }

  loadUsers() {
    this.http.get<User[]>('http://localhost:8000/users', this.auth.authOptions).subscribe({
      next: (users) => this.users.set(users),
      error: () => this.users.set([]),
    });
  }

  editUser(user: User) {
    this.selectedUser.set(user);
    this.isEditing.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.form.setValue({
      name: user.name,
      email: user.email,
      role: user.role,
      password: '',
    });
  }

  resetForm() {
    this.selectedUser.set(null);
    this.isEditing.set(false);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.form.reset({ name: '', email: '', role: 'lecteur', password: '' });
  }

  saveUser() {
    if (this.form.invalid || (this.isEditing() === false && !this.form.controls.password.value)) {
      this.errorMessage.set('Please fill in all required fields.');
      return;
    }

    this.saving.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');

    const body: any = {
      name: this.form.controls.name.value,
      email: this.form.controls.email.value,
      role: this.form.controls.role.value,
    };

    const password = this.form.controls.password.value;
    if (password) {
      body.password = password;
    }

    if (this.isEditing() && this.selectedUser()) {
      this.http.put<User>(`http://localhost:8000/users/${this.selectedUser()!.id}`, body, this.auth.authOptions).subscribe({
        next: (updated) => {
          this.successMessage.set('User updated successfully.');
          this.saving.set(false);
          this.loadUsers();
          this.editUser(updated);
        },
        error: (err) => {
          this.saving.set(false);
          this.errorMessage.set(err.error?.detail || 'Unable to update user.');
        },
      });
      return;
    }

    this.http.post<User>('http://localhost:8000/users', body, this.auth.authOptions).subscribe({
      next: (created) => {
        this.successMessage.set('User created successfully.');
        this.saving.set(false);
        this.loadUsers();
        this.resetForm();
      },
      error: (err) => {
        this.saving.set(false);
        this.errorMessage.set(err.error?.detail || 'Unable to create user.');
      },
    });
  }

  deleteUser(userId: number) {
    if (!confirm('Delete this user permanently?')) {
      return;
    }

    this.http.delete(`http://localhost:8000/users/${userId}`, this.auth.authOptions).subscribe({
      next: () => {
        if (this.selectedUser()?.id === userId) {
          this.resetForm();
        }
        this.loadUsers();
      },
      error: () => {
        this.errorMessage.set('Unable to delete user.');
      },
    });
  }

  navigateHome() {
    this.router.navigate(['/dashboard']);
  }
}
