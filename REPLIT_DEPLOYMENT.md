# Quick Start: Deploying to Replit

This guide helps you deploy the Omi project to Replit with optimized repository size.

## 🚀 Quick Deploy (Recommended)

### Step 1: Import with Shallow Clone

When creating a new Repl from this GitHub repository, Replit will automatically use a shallow clone, which significantly reduces the size.

**Just click "Import from GitHub" and paste:**
```
https://github.com/Johnsonbros/omi
```

### Step 2: Download Required Files (if needed)

If you're working with the Swift SDK or need ML models:

```bash
# Run the helper script
bash scripts/download-ml-models.sh
```

This will download the Whisper model (~75MB) needed for local transcription.

### Step 3: Start the Application

The `.replit` configuration is already set up. Just click "Run"!

## 📦 What's Excluded

The `.replitignore` file automatically excludes:

- ✅ Git history (saves ~400MB)
- ✅ Documentation files (saves ~74MB)
- ✅ Hardware design files (saves ~42MB)
- ✅ Development files (.github, .gemini)
- ✅ Test files
- ✅ Build artifacts (will be generated fresh)

**Result:** Deployment size is ~200-400MB instead of 1GB+

## 🔧 Configuration

### Environment Variables

Make sure to set these in Replit Secrets:

```bash
# Required for different features
HUME_API_KEY=your_hume_api_key
OMI_APP_ID=your_omi_app_id
OMI_API_KEY=your_omi_api_key
OPENAI_API_KEY=your_openai_key
# ... other keys as needed
```

See `web/frontend/.env.template` and `zeke-core/app/.env.template` for full list.

### Workflows

The project includes several workflows defined in `.replit`:

1. **Zeke Core API** - Backend API server (port 8000)
2. **Zeke Dashboard** - Frontend dashboard (port 5000)
3. **Redis Server** - Caching (port 6379)
4. **Celery Worker** - Background tasks

## 📊 Size Breakdown

| Component | Size | Included in Deployment |
|-----------|------|----------------------|
| Core Code | 200MB | ✅ Yes |
| Git History | 457MB | ❌ No (with .replitignore) |
| Documentation | 74MB | ❌ No (with .replitignore) |
| Hardware Files | 42MB | ❌ No (with .replitignore) |
| Tests | 20MB | ❌ No (with .replitignore) |
| **Total Deployment** | **~200MB** | **✅ Under 8GB limit** |

## 🎯 Features Available

All features work normally. The excluded files are only:

- **Videos** - Demo and tutorial videos (not needed for runtime)
- **ML Models** - Can be downloaded on-demand with the helper script
- **Hardware** - CAD files and designs (not needed for software)
- **Docs** - Developer documentation (available on GitHub)

## 🆘 Troubleshooting

### "File too large" error

If you still get file size errors:

1. Make sure you're using a shallow clone (Replit does this automatically)
2. Check that `.replitignore` is present in the root
3. Ensure you haven't added large files to git locally

### Missing ML models

If you need the Whisper model for Swift SDK:

```bash
bash scripts/download-ml-models.sh
```

### Need excluded files?

See `DEPLOYMENT.md` for details on:
- Where to download ML models
- How to access demo videos
- How to get hardware design files

## 📚 Further Reading

- **DEPLOYMENT.md** - Comprehensive deployment guide
- **README.md** - Project overview and setup
- **replit.md** - Replit-specific documentation

## 💬 Support

Having issues? Check:

1. Replit status page for any service issues
2. GitHub Issues for known problems
3. Project documentation in the docs/ directory (on GitHub)

---

**Ready to deploy!** 🎉

The repository is optimized and ready for Replit. Just import from GitHub and run!
