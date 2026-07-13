import { HttpHeaders } from '@angular/common/http';
import { Injectable, computed, signal } from '@angular/core';
import { Router } from '@angular/router';

interface JwtPayload {
  sub?: string;   // email
  role?: string;
  user_id?: number;
  exp?: number;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private tokenSignal = signal<string | null>(typeof window !== 'undefined' ? localStorage.getItem('access_token') : null);
  readonly role = computed(() => this.decodePayload(this.tokenSignal())?.role ?? null);
  readonly email = computed(() => this.decodePayload(this.tokenSignal())?.sub ?? null);
  readonly userId = computed(() => this.decodePayload(this.tokenSignal())?.user_id ?? null);

  constructor(private router: Router) {}

  get token() {
    return this.tokenSignal();
  }

  get isAuthenticated() {
    return Boolean(this.tokenSignal());
  }

  get authHeaders(): HttpHeaders | undefined {
    return this.tokenSignal() ? new HttpHeaders({ Authorization: `Bearer ${this.tokenSignal()}` }) : undefined;
  }

  get authOptions() {
    return this.authHeaders ? { headers: this.authHeaders } : undefined;
  }

  setToken(token: string) {
    localStorage.setItem('access_token', token);
    this.tokenSignal.set(token);
  }

  clear() {
    localStorage.removeItem('access_token');
    this.tokenSignal.set(null);
  }

  logout() {
    this.clear();
    this.router.navigate(['/']);
  }

  private decodePayload(token: string | null): JwtPayload | null {
    if (!token) return null;
    const segments = token.split('.');
    if (segments.length !== 3) return null;
    try {
      return JSON.parse(atob(this.padBase64(segments[1]))) as JwtPayload;
    } catch {
      return null;
    }
  }

  private padBase64(value: string) {
    return value.padEnd(value.length + (4 - (value.length % 4)) % 4, '=');
  }
}
