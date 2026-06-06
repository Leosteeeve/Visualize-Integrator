# Deployment Guide

## GitHub Pages frontend

Use the `docs` folder as the GitHub Pages publishing source.

1. Push the repository to GitHub.
2. Open the repository on GitHub.
3. Go to `Settings` -> `Pages`.
4. Set `Source` to `Deploy from a branch`.
5. Set `Branch` to `main` and `Folder` to `/docs`.
6. Save and wait for GitHub to publish the site.

If the site looks unstyled, make sure `docs/index.html` links to `styles.css` and `app.js` with relative paths, not `/styles.css` and `/app.js`.

## Render backend

Render is the simplest first backend target for this project because it can deploy a Python web service directly from GitHub.

This repository includes `render.yaml`, so you can deploy it as a Render Blueprint.

1. Push `backend/server.py`, `requirements.txt`, and `render.yaml` to GitHub.
2. Open Render and create a new Blueprint from your GitHub repository.
3. Render should detect `render.yaml`.
4. Deploy the service.
5. After deployment, open:

```text
https://YOUR-SERVICE.onrender.com/api/health
```

You should see:

```json
{"ok": true, "service": "calculus-studio"}
```

## Connect Pages to the backend

After Render gives you a backend URL, you can test it without editing code:

```text
https://YOUR-GITHUB-USER.github.io/YOUR-REPO/?api=https://YOUR-SERVICE.onrender.com
```

The page stores that API URL in `localStorage`, so later visits can continue using it.

For a permanent setup, edit `docs/index.html`:

```html
<script>
  window.CALCULUS_API_BASE = "https://YOUR-SERVICE.onrender.com";
</script>
```

Then commit and push.

## Notes

- GitHub Pages only serves static files. It cannot run the Python backend.
- The backend reads the cloud platform's `PORT` environment variable and binds to `0.0.0.0` when deployed.
- CORS is enabled so GitHub Pages can call the backend API.
- If the C++ helper is unavailable on the cloud host, the backend falls back to the Python/SciPy path.
