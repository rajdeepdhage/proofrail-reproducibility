# Publishing the Repository Using Only a Web Browser

No Git, no Terminal, no software to install. Everything below happens in
github.com and your file manager.

Total time: about 25 minutes, plus a few minutes waiting for automated checks.

Steps 1–7 put the repository online. Steps 8–11 finish the citation metadata.
Step 12 updates the thesis.

---

## Before you start

You need a GitHub account (<https://github.com/signup>) and the unzipped folder
`proofrail-reproducibility` on your computer.

### One thing to do first: reveal hidden files

Three items in the folder begin with a dot, which means your file manager hides
them by default. **If you skip this step, the automated checks will not run and
Git will not ignore the right files.**

- **macOS Finder:** open the `proofrail-reproducibility` folder and press
  **Command + Shift + Period (.)**. Hidden items appear, greyed out.
- **Windows File Explorer:** **View** menu → tick **Hidden items**.

You should now see `.github`, `.gitattributes`, and `.gitignore` alongside the
visible files.

---

## Step 1 — Confirm the repository URL (already filled in)

This has been done for you. `CITATION.cff` already records your repository URL:

```yaml
version: 0.1.0
repository-code: "https://github.com/rajdeepdhage/proofrail-reproducibility"
```

You can open the file in a plain text editor to confirm, but no edit is needed.
The same URL is already recorded in `docs/thesis_availability_statement.md`.

The only value still outstanding anywhere is the DOI, which cannot exist until
you publish a release. You will add it in step 10.

---

## Step 2 — Create the repository on GitHub

1. Go to <https://github.com/new>.
2. **Repository name:** `proofrail-reproducibility`
3. **Description:** `Reproducibility package for "Programmable Settlement Without Tokenization" (MBA thesis, UC Riverside)`
4. **Visibility:** choose **Private**. You will switch it to public in step 7,
   after checking that everything looks right. Switching is one click.
5. **Leave all three initialization boxes unticked** — do not add a README, a
   .gitignore, or a license. The folder already contains all three, and letting
   GitHub create them will conflict with your upload.
6. Click **Create repository**.

You will land on a mostly empty page with setup instructions. Ignore the command
line instructions entirely.

---

## Step 3 — Decide how you will upload

The next step offers three methods. Read them before starting, and pick one:

- **Method A, github.dev** — fully browser-based, handles folders reliably, no
  installation. Recommended.
- **Method B, drag-and-drop upload** — works in Chrome, Edge, and Firefox only.
- **Method C, GitHub Desktop** — a small application, most forgiving if the
  others misbehave.

Whichever you choose, the result is identical.

---

## Step 4 — Upload the files

GitHub's plain upload page has a real limitation: the **"choose your files"**
link opens a file picker that cannot select folders, and folder drag-and-drop
fails in Safari. If you cannot upload folders, use Method A below — it is fully
browser-based and handles folders properly.

### Method A — github.dev (recommended, no installation)

`github.dev` is a full editor that runs inside your browser, provided free by
GitHub. It accepts folders.

1. Go to your repository page and press the full stop key: **.**
   (Or change `github.com` to `github.dev` in the address bar.)
   A dark editor opens, with an **Explorer** panel down the left side.
2. Open your `proofrail-reproducibility` folder in Finder or File Explorer.
3. **Select everything inside it** — all the loose files and all the folders —
   and drag the selection into the empty Explorer panel on the left.
   Folder structure is preserved. Wait for the file tree to fill in.
4. Click the **Source Control** icon in the far-left toolbar (the branching-lines
   icon, third one down), or press **Ctrl+Shift+G** / **Cmd+Shift+G**.
5. You will see every file listed as a change. In the message box at the top,
   type `Initial release: reproducibility package v0.1.0`.
6. Click the **✓ Commit** button, then confirm **Yes** if it asks about staging
   all changes.
7. Wait for the count to reach zero, then close the tab.

Your repository now has everything, with the folder structure intact.

### Method B — drag folders in Chrome, Edge, or Firefox

The standard upload page does accept folders, but only by dragging, and only in
these browsers — **not Safari**.

1. Open `https://github.com/rajdeepdhage/proofrail-reproducibility/upload/main`
   in Chrome, Edge, or Firefox.
2. Do **not** click "choose your files" — that picker cannot take folders.
   Instead drag the folders from your file manager onto the dashed drop area.
3. Upload in batches so nothing times out:
   - **Batch 1:** all the loose files at the top level (`.gitattributes`,
     `.gitignore`, `CHANGELOG.md`, `CITATION.cff`, `CONTRIBUTING.md`,
     `DATA_ACCESS.md`, `LICENSE`, `LICENSE-CODE`, `LICENSE-DATA`,
     `MANIFEST.sha256`, `Makefile`, the two `PUBLISHING_GUIDE` files,
     `README.md`, `REPRODUCE.md`). Commit message:
     `Add project metadata and documentation`.
   - **Batch 2:** the `.github` folder. Commit: `Add automated verification workflows`.
   - **Batch 3:** `benchmark` and `knime`. Commit: `Add benchmark data, logs, results, and KNIME workflows`.
   - **Batch 4:** `docs`, `generator`, `metrics`, `scripts`, `spss`, `tests`,
     `verifier`. Commit: `Add analysis code, verifier, and documentation`.

### Method C — GitHub Desktop (one small installation, most forgiving)

If both methods above give you trouble, GitHub Desktop is a normal application
with no command line.

1. Download from <https://desktop.github.com> and sign in with your GitHub
   account.
2. **File → Clone repository → GitHub.com**, choose
   `proofrail-reproducibility`, and pick a location to save it.
3. Open the cloned folder in Finder or File Explorer. It will contain only a
   hidden `.git` folder.
4. Copy everything from inside your `proofrail-reproducibility` folder into it.
5. Return to GitHub Desktop. Every file appears as a change on the left. Type
   the summary `Initial release: reproducibility package v0.1.0` and click
   **Commit to main**.
6. Click **Push origin** at the top.

---

## Step 5 — Confirm everything arrived

Go to the repository's main page and check:

- The README renders below the file list, showing the title, the artifact-status
  note, and the results table.
- The file tree shows: `.github`, `benchmark`, `docs`, `generator`, `knime`,
  `metrics`, `scripts`, `spss`, `tests`, `verifier`, plus the loose files.
- The right sidebar shows **MIT** under "License".

To count files, click any folder and check its contents against your local copy.
The total should be 96.

If a folder is missing, repeat step 4 for that folder alone — uploading again
does not duplicate anything already present.

---

## Step 6 — Watch the automated checks run

Click the **Actions** tab. A workflow named **verify** should be running or
finished. It tests on two versions of Python and runs all nine reproducibility
checks.

**Expect a green checkmark.** If you click into the run, you will see the checks
listed one by one, ending with `ALL CHECKS PASSED`.

This is the single most valuable thing in the repository. It proves to your
committee, and to any journal reviewer, that your analysis reproduces on a
clean machine that has never seen your laptop.

If you see a red X, see **Troubleshooting** at the end.

---

## Step 7 — Make the repository public

**Settings** (top of the repository) → scroll to the bottom, **Danger Zone** →
**Change repository visibility** → **Change to public** → type the repository
name to confirm.

Do this once steps 5 and 6 look right. The thesis will cite this URL, so it must
be reachable by your committee and by reviewers.

---

## Step 8 — Create a release

A release is a fixed snapshot that can be cited and downloaded as one file.

1. On the repository main page, find **Releases** in the right sidebar and click
   **Create a new release**.
2. Click **Choose a tag**, type `v0.1.0`, and select **Create new tag: v0.1.0 on
   publish**.
3. **Release title:** `ProofRail Reproducibility Package v0.1.0`
4. **Description:** open `CHANGELOG.md` in the repository, copy the `v0.1.0`
   section, and paste it here.
5. Click **Publish release**.

---

## Step 9 — Get a permanent DOI from Zenodo

A DOI is a permanent identifier that survives even if the GitHub URL changes.
Journals expect one; your committee will find it reassuring.

1. Go to <https://zenodo.org> and click **Sign in → Sign in with GitHub**.
   Authorize the connection.
2. Click your name (top right) → **GitHub**.
3. Find `proofrail-reproducibility` in the list and switch its toggle to **On**.
4. **Important:** Zenodo only archives releases created *after* you switch the
   toggle on. Since you already published `v0.1.0` in step 8, go back to GitHub
   and publish a second release tagged `v0.1.1` (title:
   `ProofRail Reproducibility Package v0.1.1`, description: `Archival release for DOI`).
   Alternatively, switch the toggle on *before* step 8 and skip this.
5. Wait a minute, then refresh the Zenodo page. Your release appears with a DOI
   like `10.5281/zenodo.1234567`.

Zenodo issues two DOIs: a **version DOI** for that specific release and a
**concept DOI** covering all versions. **Cite the version DOI in your thesis**,
so a reader retrieves exactly the artifacts your results came from.

---

## Step 10 — Record the DOI in the repository

1. In the repository, click `CITATION.cff`.
2. Click the **pencil icon** (Edit this file) at the top right.
3. Below the `repository-code:` line you added in step 1, add:

```yaml
doi: "10.5281/zenodo.1234567"
date-released: 2026-08-11
```

Use your actual DOI and today's date.

4. Scroll down, enter the commit message `Record Zenodo DOI and release date`,
   and click **Commit changes**.

---

## Step 11 — Refresh the integrity manifest

You just edited a tracked file, which means `MANIFEST.sha256` — the file that
records a fingerprint of every artifact — is now out of date. The verification
checks will fail until it is refreshed.

Normally you would refresh it by running a script. Because you are working in the
browser, run it on GitHub instead:

1. Click the **Actions** tab.
2. In the left sidebar, click **update manifest**.
3. Click **Run workflow** → **Run workflow** (green button).
4. Wait about a minute and refresh. The workflow regenerates the manifest,
   re-runs all nine checks, and commits the updated manifest for you.

Then click back to **Actions** and confirm the **verify** workflow is green
again.

> Repeat this step any time you edit a file through the web interface.

---

## Step 12 — Update the thesis

Two placeholders in your chapters need the real values now:

1. **Chapter 2, Section 2.8** — replace
   `https://github.com/rajdeepdhage/proofrail-reproducibility` with your real URL,
   and add the DOI.
2. **Chapter 2, Section 2.3.1** — replace
   `[confirm exact date range against the archived queries]` with the actual 2024
   date bounds from your BigQuery `WHERE` clauses.

Then open `docs/thesis_availability_statement.md` in the repository, copy the
full statement, and paste it into your thesis front matter, filling in the same
URL and DOI.

---

## Making changes later

To edit a file: click it, click the pencil icon, edit, and commit.

To add or replace files: **Add file → Upload files**, drag them in, and commit.
Uploading a file with the same name and path replaces it.

To delete a file: click it, click the trash icon, and commit.

**After any change, run the "update manifest" workflow (step 11)**, then check
that **verify** is green.

If a change is significant — for example, re-running the replay at a larger
sample size — publish a new release (`v0.2.0`) and Zenodo will mint a new
version DOI automatically.

---

## Troubleshooting

**The `.github` folder is not visible when I try to drag it.**
You skipped the hidden-files step. macOS: Command + Shift + Period. Windows:
View → Hidden items.

**A red X on the verify workflow.**
Click the failed run and read which of the nine checks failed. Almost always it
is check 1, the manifest, because a file was edited without refreshing it. Fix by
running the **update manifest** workflow (step 11).

**Upload seems stuck or fails partway.**
Upload fewer files at once. Uploading a folder that is already partly present is
safe — matching files are simply replaced.

**"This file is too large" during upload.**
Should not occur; the largest file here is about 1.2 MB against a 25 MB browser
limit. If you see it, you may be uploading the wrong folder — check you are not
including a `.git` folder or a zip archive.

**I want to check things without a terminal but more thoroughly.**
Press the full stop key (`.`) while viewing the repository on GitHub. This opens
a browser-based editor where you can search and read every file. It cannot run
the scripts, but it is useful for reviewing content.
