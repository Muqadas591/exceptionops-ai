# Free-Tier Deployment

This deployment runs the React frontend and FastAPI backend together in one
Docker service on Render, with PostgreSQL hosted by Neon. Render's free web
service can sleep when idle, and its filesystem is temporary. Do not use it
for real invoices or other sensitive documents. Uploaded files can be lost
when the service restarts; use only synthetic data for this trial.

## 1. Push the deployment files to GitHub

Commit and push the deployment changes to the repository's `main` branch.
Keep `.env` and all credentials out of Git.

## 2. Create a free PostgreSQL database

Create a project at [Neon](https://neon.tech), then copy its PostgreSQL
connection string. Keep it private. When adding it to Render, use the
SQLAlchemy driver prefix `postgresql+psycopg://` rather than `postgresql://`,
and retain any SSL query parameters supplied by Neon.

## 3. Deploy the Render Blueprint

In [Render](https://render.com), create a new Blueprint and connect this
GitHub repository. Render reads `render.yaml` and creates the free web
service. When prompted, set `DATABASE_URL` to the Neon connection string.
Render generates `AUTH_SECRET_KEY`; do not replace it with a value committed
to the repository.

The service runs database migrations on startup. Its readiness check verifies
both the database connection and temporary document storage. Once the deploy
is healthy, Render shows the public `onrender.com` URL; opening it displays
the application login page. Render's runtime hostname is automatically added
to the trusted-host and CORS settings.

## 4. Create your first administrator

The app has no public signup, so create an administrator against the Neon
database before signing in. From the project directory on a machine with the
project dependencies installed, set `DATABASE_URL` to the same private Neon
connection string and run:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://..."
python -m scripts.create_user --email you@example.com --role admin
Remove-Item Env:DATABASE_URL
```

The script prompts for a password and stores only its password hash. Do not
share this administrator account; create a separate, least-privileged
demonstration account if you want to share sign-in access.

## Limitations

- The free web service may take time to respond after being idle.
- The service's local document directory is not persistent. Uploaded files
  can disappear after a restart or redeploy.
- Neon and Render free-tier limits and availability are controlled by their
  providers and may change.
- A public URL does not make the app publicly usable without an account.
- Use synthetic demonstration data only; simulated actions are not real
  payments or external transactions.
