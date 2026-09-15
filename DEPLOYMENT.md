# StockChain Deployment Guide

## Architecture
- **Frontend (Angular)** → GoDaddy shared hosting (static files)
- **Backend (FastAPI)** → Render.com free web service
- **Database (PostgreSQL)** → Render.com free PostgreSQL

---

## Part 1: Deploy Backend to Render.com

### 1. Push code to GitHub
Create a GitHub repository and push the entire project:
```powershell
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/stockchain.git
git push -u origin main
```

> **Important:** Make sure `.env` is in `.gitignore` so your local passwords are not committed.

### 2. Create Render account
Go to [https://render.com](https://render.com) and sign up with your GitHub account.

### 3. Deploy using render.yaml (Blueprint)
1. In Render dashboard → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render will detect `render.yaml` and create:
   - A PostgreSQL database named `stockdb`
   - A web service named `stockchain-backend`

### 4. Set the ALLOWED_ORIGINS variable
After deployment, go to the `stockchain-backend` service → **Environment** tab:
- Set `ALLOWED_ORIGINS` to your GoDaddy domain, e.g.:
  ```
  https://www.yourdomain.com,https://yourdomain.com
  ```

### 5. Get your Render backend URL
After deploy succeeds, your backend URL will be:
```
https://stockchain-backend.onrender.com
```
Keep this URL — you need it in the next step.

---

## Part 2: Build Angular Frontend for Production

### 1. Update the production API URL
Edit `frontend/src/environments/environment.prod.ts`:
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://stockchain-backend.onrender.com'  // ← your Render URL
};
```

### 2. Build for production
```powershell
cd frontend
npm install
ng build --configuration production
```

The built files will be in:
```
frontend/dist/stockchain-frontend/browser/
```

---

## Part 3: Upload Frontend to GoDaddy

### 1. Log in to GoDaddy cPanel
Go to your GoDaddy account → My Products → Web Hosting → Manage → cPanel

### 2. Open File Manager
In cPanel → **File Manager** → navigate to `public_html/`

### 3. Upload files
Upload **all contents** of `frontend/dist/stockchain-frontend/browser/` into `public_html/`.

The folder should contain:
- `index.html`
- `*.js` files
- `*.css` files

### 4. Create `.htaccess` for Angular routing
In `public_html/`, create a file named `.htaccess` with this content:
```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```
This ensures Angular's client-side routing works correctly.

### 5. Visit your site
Go to `https://yourdomain.com` — the Angular app should load and call the Render backend.

---

## Part 4: Migrate Your PostgreSQL Data to Render

After Render creates the database, you need to import your local data.

### Export from local PostgreSQL
```powershell
pg_dump -U postgres -d stockDB -f stockdb_backup.sql
```

### Import to Render PostgreSQL
Get the **External Database URL** from Render dashboard → stockdb → Connection details, then:
```powershell
psql "YOUR_RENDER_EXTERNAL_DATABASE_URL" -f stockdb_backup.sql
```

---

## Environment Variables Summary

### Render Backend (`stockchain-backend` service)
| Variable | Value |
|---|---|
| `DATABASE_URL` | Auto-set from Render PostgreSQL |
| `ALLOWED_ORIGINS` | `https://yourdomain.com,https://www.yourdomain.com` |

### Local Development (`.env` file)
| Variable | Value |
|---|---|
| `DATABASE_URL` | `postgresql://postgres:Jayan@123@localhost:5432/stockDB` |
| `ALLOWED_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` |
