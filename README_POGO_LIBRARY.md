
Pokémon GO Events Digest (No-Tech Setup)

This repo automatically builds a Pokémon GO events digest from official sources and puts the results right here for you to download on your phone or computer.

You’ll get:
	•	POGO_Digest.xlsx — an Excel/Sheets file with all events (Community Days, Mega/5★ raids, Spotlights, etc.).
	•	POGO_Events.ics — a calendar you can add to your phone/calendar app.

You don’t need to code or use Colab. GitHub runs everything for you.

⸻

What’s inside this repo
	•	build_pogo_library.py — collects event pages.
	•	digest_from_library.py — makes the Excel + calendar.
	•	.github/workflows/pogo-digest.yml — tells GitHub when/how to run the scripts.
	•	outputs/latest/ — always contains the newest Excel + calendar (after each run).

⸻

One-time setup (5 minutes)

You can do this in the GitHub mobile app or the github.com website.
If you already see a file named .github/workflows/pogo-digest.yml, skip to Run it now.

A) Create the workflow file

On the GitHub app (iOS/Android):
	1.	Open your repository.
	2.	Tap the + → Add file → Create new file.
	3.	Name it (type exactly):

.github/workflows/pogo-digest.yml


	4.	Paste in the workflow content your helper provided (the “POGO Events Digest” YAML).
	5.	Tap Commit changes.

On the GitHub website:
	1.	Go to your repo → click Add file → Create new file.
	2.	Name it:

.github/workflows/pogo-digest.yml


	3.	Paste the workflow content.
	4.	Click Commit changes.

That’s it. GitHub now knows how to build your digest.

⸻

Run it now (on demand)

You can run it whenever you want (and it also runs automatically every month):

App or Website:
	1.	Open your repo → Actions tab.
	2.	Tap/Click POGO Events Digest.
	3.	Tap/Click Run workflow (green button).
It will take a few minutes. You can leave the app; it runs in the cloud.

⸻

Where to get your files

After the run finishes, your files are in three places. Use whichever is easiest:
	1.	outputs/latest/ (always up to date)
	•	Repo → browse to outputs/latest/
	•	Download POGO_Digest.xlsx and POGO_Events.ics
	•	This folder always holds the newest files.
	2.	Actions → Artifacts (downloadable ZIP)
	•	Repo → Actions → open the latest run
	•	Scroll to Artifacts → download
	•	Unzip to get the .xlsx and .ics files.
	3.	Releases (optional)
	•	Repo → Releases → open the newest release
	•	Download the attached files

⸻

How to use the files

Add the calendar on iPhone (ICS)
	1.	From GitHub (app or web), download POGO_Events.ics.
	2.	Open the file on your phone → choose Add to Calendar (Apple Calendar)
(For Google Calendar: upload the .ics via calendar.google.com on a computer, or import to a Google account and it will sync to your phone.)

Open the Excel digest
	•	iPhone/iPad: Open POGO_Digest.xlsx in Files, Excel app, or Google Sheets.
	•	Computer: Open in Excel, Numbers, or upload to Google Drive and open in Google Sheets.

Tips in the Excel file:
	•	Filter by Category (Community Day, Raid/Mega, Spotlight, etc.).
	•	Sort by Start Date to see what’s coming next.

⸻

What the workflow does (in plain English)

Every time it runs, GitHub will:
	1.	Collect events from trusted sources (Niantic blog + Leek Duck pages).
	2.	Build a library of those pages.
	3.	Create:
	•	POGO_Digest.xlsx (spreadsheet of all events)
	•	POGO_Events.ics (calendar)
	4.	Save the newest files to outputs/latest/ in this repo.
	5.	Upload artifacts and optionally publish a release for easy downloads.

You don’t have to do anything except press Run workflow when you want an update (or wait for the monthly schedule).

⸻

Running on a schedule (automatic)

By default, it runs on the 1st of each month at 09:00 UTC.
You can still Run workflow manually any time (e.g., after big news).

If you ever want a different schedule, ask your helper to update the line in the YAML that says:

cron: "0 9 1 * *"

to a time you prefer.

⸻

Troubleshooting (quick fixes)
	•	I don’t see the workflow in Actions
	•	Make sure the file exists at:
.github/workflows/pogo-digest.yml
	•	Commit it to your main branch (usually main).
	•	The run failed / turned red
	•	Open the run → click the failed step to see the message.
	•	Most common quick fix: run it again later (network hiccup).
	•	No Releases?
	•	That’s OK — your files are still in outputs/latest/ and Artifacts.
	•	Releases can be re-enabled/fixed later; not required to use the files.
	•	I can’t find the files on my phone
	•	In the GitHub app, browse your repo’s folders to: outputs/latest/
	•	Tap a file → Download (or Open in… to share to Calendar/Excel/Sheets).

⸻

Frequently asked

Q: Is this safe to run from my phone?
A: Yes. You’re not running code on your phone — GitHub runs it in the cloud and puts the results in your repo.

Q: Do I need to edit any code?
A: No. The workflow file already knows what to do.

Q: Can I get shorter “just the key stuff” views?
A: Yes. Ask your helper to add a “Lite” sheet (CDs/Spotlights/Raid hours & rotations + short notes), or add local times to the calendar entries.

⸻

Need help?

If something’s confusing or you want a new feature (e.g., Google Sheets sync, “play/skip” recommendations, or time-specific calendar entries), just open an Issue in this repo or ask your helper to update the workflow.