# Deploying Sedna Academy to AWS Free Tier

This guide deploys the whole stack (Postgres + FastAPI backend + Vue frontend)
onto a single AWS Free Tier EC2 instance, behind Caddy for automatic HTTPS.
Everything below was tested end-to-end on this machine before being written
down — the production Docker images build cleanly and a real login through
the reverse proxy was confirmed working.

## Architecture

```
Internet ──HTTPS──▶ Caddy (web container, ports 80/443)
                       ├─ /api/*  → backend container (FastAPI, port 8000, internal only)
                       └─ /*      → static Vue build (served directly by Caddy)
                                        │
                                    backend ──▶ db container (Postgres, internal only)
```

One EC2 instance runs all three containers via `docker-compose.prod.yml`.
Only ports 80/443 are exposed to the internet — Postgres and the backend
are reachable only from other containers on the same Docker network.

## What's in AWS Free Tier (12 months from account creation)

- **EC2**: 750 hours/month of `t2.micro` or `t3.micro` (enough for one
  instance running 24/7) + 30GB of EBS storage.
- That's it for this deployment — everything else (Postgres, backups) runs
  on that one instance, so there's no separate RDS bill to track.
- After 12 months, a `t3.micro` costs roughly $7–8/month on-demand.

**Why not RDS for Postgres?** RDS free tier exists too, but running Postgres
in a container on the same box is simpler to reason about, avoids a second
service's free-tier clock, and this app already runs that way in dev. If you
outgrow a single instance later, migrating to RDS is a `DATABASE_URL` change
away — nothing in the app assumes a local database.

## Prerequisites

- An AWS account (free tier eligible)
- A domain name you can point DNS at (Caddy needs this for automatic HTTPS
  — you cannot get a trusted TLS cert for a bare IP address)
- This repo pushed to a git remote you can `git clone` from the server

---

## Step 1 — Launch the EC2 instance

1. AWS Console → **EC2** → **Launch instance**.
2. **Name**: `sedna-academy`.
3. **AMI**: Ubuntu Server 24.04 LTS (free tier eligible).
4. **Instance type**: `t3.micro` (or `t2.micro` — check which is free-tier
   eligible in your account/region; both work here).
5. **Key pair**: create a new one, download the `.pem`, keep it safe — it's
   the only way to SSH in.
6. **Network settings** → **Edit** → Security group rules:
   | Type | Port | Source |
   |---|---|---|
   | SSH | 22 | **My IP** (not 0.0.0.0/0 — don't leave SSH open to the world) |
   | HTTP | 80 | Anywhere (0.0.0.0/0) |
   | HTTPS | 443 | Anywhere (0.0.0.0/0) |
7. **Storage**: 30GB gp3 (the free-tier max — more than enough).
8. Launch. Once running, note the **public IPv4 address**.
9. **(Recommended)** Allocate an **Elastic IP** and associate it with the
   instance, so the address survives a stop/start. Elastic IPs are free
   while attached to a running instance.

## Step 2 — Point your domain at it

In your DNS provider, add an **A record**:
```
academy.yourcompany.com  →  <the Elastic IP>
```
DNS propagation can take a few minutes to a few hours. You can move on while
it propagates — Caddy will simply retry until it resolves.

## Step 3 — SSH in and bootstrap the server

```bash
ssh -i /path/to/your-key.pem ubuntu@<elastic-ip>
```

Once connected:

```bash
curl -fsSL https://raw.githubusercontent.com/<your-org>/<your-repo>/main/scripts/ec2-bootstrap.sh -o bootstrap.sh
chmod +x bootstrap.sh
./bootstrap.sh
```

(If your repo is private, `scp` the script up instead, or just clone the repo
manually and run the same steps — see [scripts/ec2-bootstrap.sh](../scripts/ec2-bootstrap.sh)
for exactly what it does: installs Docker, adds a 2GB swapfile since a
`t2/t3.micro` only has 1GB RAM, and clones the repo.)

Log out and back in once it finishes (so your user picks up Docker group
permissions):

```bash
exit
ssh -i /path/to/your-key.pem ubuntu@<elastic-ip>
cd ~/sedna
```

## Step 4 — Configure environment variables

```bash
cp .env.production.example .env
nano .env
```

Fill in real values. Generate strong secrets with:

```bash
openssl rand -hex 32
```

Use a **different** random value for `POSTGRES_PASSWORD` and `SECRET_KEY`.
Set `DOMAIN`, `CORS_ORIGINS`, and `APP_URL` to your real domain
(`https://academy.yourcompany.com`), and `ADMIN_EMAIL`/`ADMIN_PASSWORD` to
the account you'll actually log in with.

Leave `EMAIL_ENABLED=false` until you have real SMTP credentials — with it
`false`, the app logs emails to the container's stdout instead of sending
them, so nothing breaks, you just won't get real invite/certificate emails
yet.

## Step 5 — Deploy

```bash
chmod +x scripts/deploy.sh scripts/backup-db.sh
./scripts/deploy.sh
```

This builds both images and starts `db`, `backend`, and `web` (Caddy).
Caddy will automatically request and install a Let's Encrypt certificate
for your domain the first time it starts — no manual certbot step. Give it
a minute; watch progress with:

```bash
docker compose -f docker-compose.prod.yml logs -f web
```

## Step 6 — Initialize the database

**First deploy only.** This creates all tables and your first admin account
from the `ADMIN_EMAIL`/`ADMIN_PASSWORD` you set in `.env`:

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.init_db
```

It's safe to re-run later — it won't duplicate tables or the admin user.

> **Note on migrations**: this repo has an `alembic/` folder but it was
> never actually initialized (empty `versions/`, no `alembic.ini`) — the
> schema is created directly via `Base.metadata.create_all` in
> `init_db.py`, same as local dev. That's fine for getting started, but
> **before you make further schema changes** (new columns, new tables) in
> production, set up a real Alembic migration chain so you can apply
> changes without data loss. Don't hand-edit the production schema.

## Step 7 — Verify

Visit `https://academy.yourcompany.com` — you should see the login page
over a valid HTTPS connection. Log in with the admin account from Step 4.

## Step 8 — Add your course content

Log in as admin → **Content** in the sidebar → **New path** to start
building your real courses. Nothing here needs further deployment steps —
content changes are just database writes through the admin UI.

---

## Ongoing operations

### Redeploying after code changes

```bash
cd ~/sedna
./scripts/deploy.sh
```

Pulls the latest code and rebuilds only what changed. No downtime for
unrelated services (Caddy keeps serving while `backend` restarts).

### Database backups

```bash
chmod +x scripts/backup-db.sh
```

Add a daily cron job:

```bash
crontab -e
```
```
0 3 * * * /home/ubuntu/sedna/scripts/backup-db.sh >> /home/ubuntu/backup.log 2>&1
```

Dumps land in `~/sedna-backups/`, gzipped, with the last 14 days kept
automatically. This is local-only — it protects against "I fat-fingered a
DELETE," not against instance loss. If you want off-instance durability,
the script has a commented-out `aws s3 sync` line (S3 free tier: 5GB/month
for 12 months) — install the AWS CLI, run `aws configure` with an IAM user
scoped to that one bucket, and uncomment it.

### Monitoring disk space

A `t2/t3.micro`'s 30GB fills up faster than you'd think once Docker images
accumulate. Check periodically:

```bash
df -h /
docker system df
```

Reclaim space from old, unused images after a deploy:

```bash
docker image prune -af
```

### Viewing logs

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f db
```

### Restarting after an instance reboot

`restart: unless-stopped` on every service means Docker Desktop's daemon
restarting the containers automatically after a reboot — no manual
intervention needed, as long as the Docker service itself is enabled
(it is, by default, after `curl -fsSL https://get.docker.com | sh`).

---

## Things worth doing next (not required to launch)

- **Generate a `frontend/package-lock.json`** (run `npm install` locally
  once and commit it) so the production build can use `npm ci` instead of
  `npm install` — faster, and guarantees the exact same dependency
  versions every build.
- **Real Alembic migrations** — see the note in Step 6.
- **CloudWatch or a simple uptime check** (e.g. UptimeRobot's free tier)
  so you find out about downtime before a customer does.
- **SMTP provider** (SES, Postmark, etc.) so certificate/invite emails
  actually send — SES is itself in AWS's free tier (62,000 emails/month
  free if sent from an EC2 instance).
- **A staging environment** — even a second, smaller EC2 instance running
  the same compose file against a separate `.env`, so schema/content
  changes get a dry run before hitting real learners.
