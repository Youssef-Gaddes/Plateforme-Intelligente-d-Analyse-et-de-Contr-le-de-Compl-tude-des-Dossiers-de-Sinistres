import { Routes } from '@angular/router';
import { AuthComponent } from './auth.component';
import { DashboardComponent } from './dashboard.component';
import { ClaimsComponent } from './claims.component';
import { UsersComponent } from './users.component';
import { ClaimCreateComponent } from './claim-create.component';
import { ClaimEditComponent } from './claim-edit.component';
import { ClaimDetailComponent } from './claim-detail.component';
import { DocumentDetailComponent } from './document-detail.component';
import { DocumentsComponent } from './documents.component';

export const routes: Routes = [
  { path: '', component: AuthComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'claims', component: ClaimsComponent },
  { path: 'claims/new', component: ClaimCreateComponent },
  { path: 'claims/:id/edit', component: ClaimEditComponent },
  { path: 'claims/:id', component: ClaimDetailComponent },
  { path: 'documents', component: DocumentsComponent },
  { path: 'documents/:id', component: DocumentDetailComponent },
  { path: 'users', component: UsersComponent },
];
