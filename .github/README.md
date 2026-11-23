# GitHub Actions Cloud Runner Guide
## Zero-Local-Load Evaluation & Artifact Generation

---

### Why Use GitHub Actions for PLE?

* **No Docker on your PC:** Runs everything in clean, high-performance Ubuntu cloud VMs.
* **16 GB RAM & Fast Bandwidth:** Downloads large Hugging Face task datasets in seconds.
* **Automated Artifacts:** The cloud runner runs the tasks, computes the engineering math, creates the deliverables, and uploads or commits them straight into `harness/artifacts/`.

---

### Step-by-Step Setup

#### 1. Push This Repository to GitHub
Create a new private GitHub repository (e.g. `ple-autonomous-engineer`) and push your workspace:
```bash
git init
git add -A
git commit -m "feat: initial autonomous agent harness and cloud evaluation workflows"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

#### 2. Add Secrets to Your GitHub Repository
1. In your GitHub repository, go to **Settings > Secrets and variables > Actions**.
2. Click **"New repository secret"** and add:
   * **`HF_TOKEN`**: Your Hugging Face read token (`hf_...`).
   * **`GEMINI_API_KEY`** (optional): Your Gemini API key if testing with Gemini directly.
   * **`OPENAI_API_KEY`** (optional): Your OpenAI key if testing with OpenAI models.

---

### How to Run Cloud Workflows

#### A. Quick Smoke Test (`Validate Harness`)
* Triggered automatically whenever you push code changes to `harness/`.
* Or manually trigger it:
  1. Go to the **Actions** tab on GitHub.
  2. Select **Validate Harness (Smoke Test)**.
  3. Click **"Run workflow"**.

#### B. Run Engineering Tasks & Generate Artifacts (`Run PLE Evaluation`)
1. Go to the **Actions** tab on GitHub.
2. Select **Run PLE Evaluation & Generate Artifacts**.
3. Click **"Run workflow"**.
4. You can configure:
   * **Task IDs:** Enter a specific task (e.g., `engineers-estimate-check` or `data-center-site-model`) or type `all` to run the full 29-task suite.
   * **Trials:** Number of concurrent tasks (default `2`).
   * **Commit Artifacts:** Check the box to have the cloud runner automatically commit the output files into `harness/artifacts/`.
5. Once finished, you can also download the complete artifacts zip from the workflow run summary!
