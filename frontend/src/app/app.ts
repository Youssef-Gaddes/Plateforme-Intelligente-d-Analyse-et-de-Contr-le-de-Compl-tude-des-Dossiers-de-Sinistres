import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-root',
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrls: ['./app.css']
})
export class App {
  private auth = inject(AuthService);
  protected readonly title = signal('project_name');

  get isAuthenticated() {
    return this.auth.isAuthenticated;
  }

  get role() {
    return this.auth.role();
  }

  get email() {
    return this.auth.email();
  }

  get userInitial() {
    const e = this.auth.email();
    return e ? e.charAt(0).toUpperCase() : '?';
  }

  logout() {
    this.auth.logout();
  }
}
