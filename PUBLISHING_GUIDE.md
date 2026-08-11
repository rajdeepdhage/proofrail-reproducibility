# Step-by-Step: Publishing the ProofRail Reproducibility Repository

Everything in the zip is verified and ready. Follow these steps in order. Steps
1–6 get the repository online; steps 7–9 finish the citation metadata; step 10
updates the thesis.

Total time: about 20 minutes, plus a few minutes waiting for CI.

---

## Before you start

You need:

- A GitHub account.
- Git installed. Check by opening Terminal and running `git --version`. If it is
  missing, macOS will offer to install the developer tools when you run it, or
  download from <https://git-scm.com/downloads>.
- The zip: `proofrail-reproducibility.zip`.

One-time Git setup, if you have never used Git on this machine:

```bash
git config --global user.name "Rajdeep Dhage"
git config --global user.email "your-github-email@example.com"
```

Use the same email as your GitHub account so commits are attributed to you.

---

## Step 1 — Unzip and check locally

```bash
cd ~/Documents
unzip proofrail-reproducibility.zip
cd proofrail-reproducibility
bash scripts/verify.sh
```

**Expect:** nine checks, ending in `ALL CHECKS PASSED`.

Do not continue if this fails. It passed when packaged, so a failure here means
something was altered or the unzip was incomplete.

---

## Step 2 — Create the repository on GitHub

1. Go to <https://github.com/new>.
2. **Repository name:** `proofrail-reproducibility`
3. **Description:** `Reproducibility package for "Programmable Settlement Without Tokenization" (MBA thesis, UC Riverside)`
4. **Visibility:** choose **Private** for now. You will make it public in step 6,
   after you have seen it render and CI pass. Flipping to public is one click.
5. **Do not** tick "Add a README file", "Add .gitignore", or "Choose a license".
   The repository already contains all three, and letting GitHub create them
   causes a conflict on your first push.
6. Click **Create repository**.

Leave the page open — it shows the URL you need next.

---

## Step 3 — Connect your local folder and push

From inside the `proofrail-reproducibility` folder:

```bash
git init
git add .
git commit -m "Initial release: reproducibility package v0.1.0"
git branch -M main
git remote add origin https://github.com/rajdeepdhage/proofrail-reproducibility.git
git push -u origin main
```

This is already filled in with your username.

**Authentication note:** GitHub no longer accepts your account password here. If
prompted, use a Personal Access Token instead: GitHub → your avatar → Settings →
Developer settings → Personal access tokens → Tokens (classic) → Generate new
token, tick the `repo` scope, copy it, and paste it as the password. Or install
GitHub Desktop (<https://desktop.github.com>) and do the push through its
interface, which handles sign-in for you.

---

## Step 4 — Confirm the upload looks right

Refresh the repository page. Check:

- The README renders, showing the title, the artifact-status note, and the
  results table.
- The file tree shows `benchmark/`, `docs/`, `generator/`, `knime/`, `metrics/`,
  `scripts/`, `spss/`, `tests/`, `verifier/`.
- The right sidebar shows **MIT** under "License" (this is why the `LICENSE`
  file was added).
- 93 files, roughly 4 MB.

---

## Step 5 — Confirm continuous integration passes

Click the **Actions** tab. A workflow named `verify` should be running or
finished, testing on Python 3.9 and 3.12.

**Expect:** a green check on both. The workflow runs `scripts/verify.sh`, which
uses only the Python standard library, so it needs no dependency installation.

A green check here is worth more than any claim in your README: it proves to any
visitor that the analysis reproduces on a clean machine, not just on yours.

---

## Step 6 — Make the repository public

Settings → scroll to **Danger Zone** → **Change repository visibility** →
**Change to public** → confirm.

Do this once steps 4 and 5 look right. The thesis will cite this URL, so it must
be reachable by your committee and by reviewers.

---

## Step 7 — Repository URL (already recorded)

No action needed. `CITATION.cff` already contains:

```yaml
repository-code: "https://github.com/rajdeepdhage/proofrail-reproducibility"
```

and `docs/thesis_availability_statement.md` carries the same URL. Only the DOI
remains, and it is added in step 9 after the release exists.

---

## Step 8 — Archive a release and mint a DOI

A DOI gives you a permanent, citable identifier that survives even if the
GitHub URL changes. Journals expect one.

1. Go to <https://zenodo.org> and sign in with your GitHub account.
2. Zenodo → your avatar → **GitHub**. Find `proofrail-reproducibility` in the
   list and switch its toggle **On**.
3. Back on GitHub: **Releases** → **Create a new release**.
   - **Tag:** `v0.1.0`
   - **Title:** `ProofRail Reproducibility Package v0.1.0`
   - **Description:** paste the `v0.1.0` section from `CHANGELOG.md`.
   - Click **Publish release**.
4. Wait a minute, then check Zenodo. The release will appear with a DOI like
   `10.5281/zenodo.XXXXXXX`.

Zenodo mints two DOIs: a *version* DOI for this specific release and a *concept*
DOI covering all versions. **Cite the version DOI in the thesis**, so a reader
retrieves exactly the artifacts your results came from.

---

## Step 9 — Record the DOI and confirm release readiness

Add to `CITATION.cff`:

```yaml
doi: "10.5281/zenodo.XXXXXXX"
date-released: 2026-08-11
```

Then:

```bash
python3 scripts/make_manifest.py
python3 scripts/check_release_readiness.py
```

**Expect:** `READY` — this gate has been failing only on the URL and DOI, both of
which now exist.

```bash
git add -A
git commit -m "Record Zenodo DOI and release date"
git push
```

---

## Step 10 — Update the thesis

Two placeholders in your chapters need the real values:

1. **Chapter 2, Section 2.8** — replace
   `https://github.com/rajdeepdhage/proofrail-reproducibility` with your real URL,
   and add the DOI.
2. **Chapter 2, Section 2.3.1** — replace
   `[confirm exact date range against the archived queries]` with the actual 2024
   date bounds from your BigQuery `WHERE` clauses.

Then paste the full availability statement from
`docs/thesis_availability_statement.md` into the thesis front matter, filling in
the same URL and DOI.

---

## Afterwards: updating the repository

When you re-run the replay at a larger sample size, or make any other change:

```bash
# make your changes, then:
bash scripts/verify.sh              # confirm everything still passes
python3 scripts/make_manifest.py    # refresh the integrity manifest
git add -A
git commit -m "Describe what changed"
git push
```

If the change is significant enough to cite differently, tag a new release
(`v0.2.0`) and Zenodo will mint a new version DOI automatically.

---

## If something goes wrong

**`git push` rejected — "remote contains work you do not have locally."**
You let GitHub create a README or license in step 2. Fix:
`git pull --rebase origin main` then push again.

**CI shows a red X.** Open Actions → click the failed run → read the step that
failed. The most likely cause is an edited file with a stale manifest: run
`python3 scripts/make_manifest.py`, commit, and push.

**`verify.sh` fails after you edit something.** That is the manifest doing its
job. Re-run `python3 scripts/make_manifest.py` to record the new state, then
verify again.

**Authentication keeps failing.** Use GitHub Desktop instead of the command
line; it handles credentials without tokens.
