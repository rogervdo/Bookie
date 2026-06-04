# Aiven CA certificate

Aiven PostgreSQL uses a project CA that is not in your Mac’s default trust store. Download it once and save it here as **`ca.pem`**.

## Steps

1. Open your Aiven service → **Connection information**.
2. Under **CA certificate**, click **Show** (or the download icon).
3. Save the file as:

   ```
   backend/certs/ca.pem
   ```

4. In `backend/.env`, keep your existing `DATABASE_URL` with `?sslmode=require` (or use `verify-full`). The app auto-detects `certs/ca.pem` and verifies TLS with that CA.

Optional override:

```bash
DATABASE_SSL_CA=./certs/ca.pem
```

`ca.pem` is gitignored — do not commit it.
