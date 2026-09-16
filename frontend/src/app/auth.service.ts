import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../environments/environment';

interface LoginResponse {
  token: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly tokenKey = 'stockchain_auth_token';
  private readonly loginEndpoint = `${environment.apiUrl}/auth/login`;

  readonly isAuthenticated = signal(this.hasStoredToken());

  constructor(private readonly http: HttpClient) {}

  private hasStoredToken(): boolean {
    return !!localStorage.getItem(this.tokenKey);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  login(username: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(this.loginEndpoint, { username, password })
      .pipe(
        tap((response) => {
          localStorage.setItem(this.tokenKey, response.token);
          this.isAuthenticated.set(true);
        }),
      );
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith('stockchain_')) {
        localStorage.removeItem(key);
      }
    }
    this.isAuthenticated.set(false);
  }
}
