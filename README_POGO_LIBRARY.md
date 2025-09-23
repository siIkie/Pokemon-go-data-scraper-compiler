# POGO Events Digest (Smart Watch)

Automated workflow that generates and publishes a digest of upcoming Pokémon GO events, formatted for quick viewing on smart watches.  

This workflow pulls live Pokémon GO event data, processes it into a compact summary, and pushes updates to a GitHub Release. The release artifacts can then be consumed by companion apps, notifications, or smart watch integrations.

---

## Features

- ⏱ Automated schedule: Runs on a cron schedule to fetch new events.  
- 🔄 Manual dispatch: Can also be triggered on-demand via the GitHub Actions UI.  
- 📦 Release management: Creates/updates a GitHub Release with the latest event digest.  
- 📲 Smart watch-friendly: Output optimized for quick glanceability on wearable devices.  

---

## Workflow Overview

1. **Fetch events** – Gathers upcoming Pokémon GO events.  
2. **Format digest** – Builds a compact summary designed for small screens.  
3. **Publish release** – Uploads the digest to a GitHub Release for easy access.  

The workflow supports both scheduled runs and manual dispatch runs.

---

## Setup

1. Ensure your repository allows workflows to write contents:  
   - Go to Settings → Actions → General → Workflow permissions.  
   - Select Read and write permissions.  

2. Confirm your workflow file `.github/workflows/pogo-digest.yml` includes:
   ```yaml
   permissions:
     contents: write
   ```

3. The release action must use the default GitHub token:
   ```yaml
   - name: Create/Update Release
     uses: ncipollo/release-action@v1
     with:
       token: ${{ secrets.GITHUB_TOKEN }}
       allowUpdates: true
   ```

---

## Usage

- **Run automatically** – The workflow executes on the set schedule to keep releases current.  
- **Run manually** – Navigate to the GitHub Actions tab, select the workflow, and click Run workflow.  

Each successful run updates the release with the latest Pokémon GO events digest.

---

## Troubleshooting

- ❌ Create/Update Release step fails →  
  - Ensure `contents: write` permission is enabled.  
  - Verify `GITHUB_TOKEN` is being passed correctly.  
  - If using a constant tag, enable `allowUpdates: true`.
