# POGO Events Digest (Smart Watch)

This project automatically creates a **digest of upcoming Pokémon GO events** and publishes it as a downloadable file on GitHub. The digest is short and glanceable — perfect for small screens, like a smart watch or phone notification.  

You don’t need to code to use it — just check the latest Release on this repo to see the current event digest.  

---

## How It Works (Quick Overview)

- Automatic Updates: Runs on a schedule to fetch upcoming events.  
- Digest Format: Events are simplified into a short list that’s easy to skim.  
- Published as a Release: Each update is added to the GitHub Releases page so it’s always easy to find.  

---

## Using It

1. Go to the Releases page in this repo.  
2. Open the latest release — the event digest will be attached.  
3. That’s it. You can view or download it however you like.  

---

## Specifics (For Developers / Curious Readers)

- The workflow file lives in `.github/workflows/pogo-digest.yml`.  
- It uses GitHub Actions to:  
  1. Fetch event data  
  2. Generate a digest  
  3. Update a GitHub Release with the digest file  
- Permissions: the workflow requires `contents: write` to update releases.  
- Release publishing uses `ncipollo/release-action` with:  
  ```yaml
  allowUpdates: true
  token: ${{ secrets.GITHUB_TOKEN }}
  ```  

---

## Future Work

The digest is designed to be lightweight and portable, which opens up some fun possibilities:  

### Notifications
- Push alerts via services like IFTTT or Zapier, so your phone pings you when new events are published.  
- GitHub’s built-in “watch releases” email notifications.  

### Companion Apps
- A simple iOS/Android app that fetches the latest digest from GitHub.  
- A widget or shortcut (iOS Shortcuts, Android Tasker) that displays the digest on your phone’s home screen.  

### Smart Watch Integration
- Show the digest directly on a watch app for Apple Watch or Wear OS.  
- Mirror notifications from phone → watch, so each new digest release automatically buzzes your wrist.  
- Advanced: embed digest text into a watch face complication that refreshes periodically.  

---

## Troubleshooting

- If the Release doesn’t update, make sure:  
  - Repository → Settings → Actions → Workflow permissions is set to Read and write.  
  - The workflow file includes:  
    ```yaml
    permissions:
      contents: write
    ```
