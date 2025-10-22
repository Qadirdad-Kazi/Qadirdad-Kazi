# 🚀 Setup Guide for Your Enhanced README

## 📋 Prerequisites

Your profile repository should be named: `qadirdad-kazi` (same as your GitHub username)

## 🐍 Setting Up the Snake Animation

The snake animation is the coolest feature! Here's how to enable it:

### Step 1: Enable GitHub Actions
1. Go to your profile repository: `https://github.com/qadirdad-kazi/qadirdad-kazi`
2. Click on **Settings** tab
3. Go to **Actions** → **General**
4. Under "Workflow permissions", select **Read and write permissions**
5. Click **Save**

### Step 2: Commit the Workflow File
The workflow file `.github/workflows/snake.yml` is already created. You need to:

```bash
git add .github/workflows/snake.yml
git commit -m "Add snake animation workflow"
git push
```

### Step 3: Run the Workflow
1. Go to **Actions** tab in your repository
2. Click on **Generate Snake Animation** workflow
3. Click **Run workflow** → **Run workflow**
4. Wait 1-2 minutes for it to complete

### Step 4: Verify
Once the workflow runs successfully, the snake animation will appear in your README!

---

## ⚙️ Optional: Removing the Snake Animation

If you don't want to set up the snake animation, simply remove these lines from your README.md:

```markdown
### 🐍 Contribution Snake

<p align="center">
  <img src="https://raw.githubusercontent.com/qadirdad-kazi/qadirdad-kazi/output/github-contribution-grid-snake-dark.svg" alt="Snake animation" />
</p>
```

---

## 📊 WakaTime Integration (Optional)

The README includes WakaTime stats. To enable this:

1. Sign up at [WakaTime.com](https://wakatime.com)
2. Install the WakaTime extension in VS Code
3. Your coding time will automatically be tracked
4. The stats will appear in your README

If you don't use WakaTime, the card will simply not load (no harm done).

---

## 🎨 Customizing Colors

### Change the Theme
All stats use the `tokyonight` theme. You can change it to:
- `radical`
- `dark`
- `merko`
- `gruvbox`
- `vue`
- `github_dark`
- `dracula`

Just replace `theme=tokyonight` with your preferred theme in the URLs.

### Change Wave Colors
Edit the wave headers by modifying `customColorList` parameter:
```
customColorList=6,11,20  (current - blue/purple gradient)
```

Popular combinations:
- `6,11,20` - Blue/Purple
- `0,2,3` - Green
- `12,15,20` - Red/Orange
- `24,27,30` - Pink/Purple

---

## 📸 Preview Before Committing

To see how your README looks:
1. Commit and push to GitHub
2. Visit: `https://github.com/qadirdad-kazi`
3. Your profile README will display

Or use [readme.so](https://readme.so/) to preview locally.

---

## 🔄 Updating Information

### Update Tech Stack
Edit line 42 in README.md - add/remove technology icons:
```
?i=js,ts,python,react,nodejs...
```

Full list of available icons: [skillicons.dev](https://skillicons.dev)

### Update Social Links
Edit the "Connect With Me" section (lines 169-185) with your actual social media links.

### Update Projects
Edit the "What I'm Working On" section to reflect your current projects.

---

## ✅ Final Checklist

- [ ] Commit all files (README.md, snake.yml)
- [ ] Push to GitHub
- [ ] Enable GitHub Actions write permissions
- [ ] Run the snake animation workflow
- [ ] Verify everything displays correctly
- [ ] Update social media links
- [ ] Customize colors if desired

---

## 🆘 Troubleshooting

**Snake animation not showing?**
- Check if the workflow ran successfully in Actions tab
- Verify write permissions are enabled
- Make sure the repository name matches your username

**Stats not loading?**
- GitHub stats API can be slow sometimes
- Try refreshing after a few minutes
- Some services may be temporarily down

**WakaTime showing error?**
- This is normal if you haven't set up WakaTime
- You can remove that section or set up WakaTime

---

## 🎉 You're All Set!

Your GitHub profile is now:
- ✨ Visually stunning
- 📊 Data-rich with multiple stats
- 🎨 Professional and modern
- 🚀 Impressive to recruiters and clients

Enjoy your enhanced profile! 🎊

