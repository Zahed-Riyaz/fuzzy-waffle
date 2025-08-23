# One-Way Sync: EvalAI → GitHub

This repository now supports **one-way synchronization** from EvalAI UI to GitHub repositories using the existing `AUTH_TOKEN` repository secret.

## How It Works

### **Sync Direction: EvalAI → GitHub (One-way)**
- ✅ **EvalAI → GitHub**: Automatic (when you update challenges in EvalAI UI)
- ❌ **GitHub → EvalAI**: Not supported (by design)

### **The Flow:**
1. **User makes changes in EvalAI UI** (title, description, evaluation details, etc.)
2. **Changes are saved to EvalAI database**
3. **Automatically triggers GitHub sync** via Celery task
4. **GitHub repository is updated** with latest changes
5. **Version control**: Every change is tracked in Git history

## Setup Requirements

### **1. Repository Secret (Already configured)**
- `AUTH_TOKEN`: Your GitHub personal access token
- **Scope**: Must have `repo` permissions to push to GitHub
- **Location**: Repository Settings → Secrets and variables → Actions

### **2. Host Configuration**
```json
{
    "token": "<evalai_user_auth_token>",
    "team_pk": "<host_team_pk>",
    "evalai_host_url": "<evalai_host_url>"
}
```

### **3. Challenge Configuration in EvalAI**
Challenge hosts configure these fields in EvalAI:
- `github_repository`: "org/repo-name"
- `github_branch`: "main" (or custom branch)
- `github_token`: Personal access token

## Benefits of One-Way Sync

### **✅ Simple & Reliable**
- **No complex webhooks** to manage
- **No conflict resolution** needed
- **Predictable behavior** - changes only flow one direction

### **✅ Automatic & Seamless**
- **No manual sync** required
- **Real-time updates** to GitHub
- **Version control** for all changes

### **✅ Production Ready**
- **Uses existing** GitHub interface
- **Celery task-based** for reliability
- **Error handling** and retry logic

## What Gets Synced

### **From EvalAI to GitHub:**
- `title` - Challenge title
- `description` - Challenge description
- `evaluation_details` - Evaluation criteria
- All challenge configuration files
- Evaluation scripts
- Challenge metadata

### **Sync Triggers:**
- Challenge creation
- Challenge updates
- Challenge phase updates
- Any field modification in EvalAI UI

## Usage

### **Automatic Setup**
When you run the challenge processing script:
1. It automatically detects your `AUTH_TOKEN`
2. Configures one-way sync from EvalAI to GitHub
3. Sets up the sync endpoints

### **Manual Configuration in EvalAI**
1. **Create/Edit Challenge** in EvalAI UI
2. **Set GitHub fields:**
   - Repository: `your-org/your-repo`
   - Branch: `main` (or your preferred branch)
   - Token: Your GitHub personal access token
3. **Save changes** - sync happens automatically

## Localhost Development

### **Works the Same Way**
- **No special configuration** needed for localhost
- **Uses same sync mechanism** as production
- **Perfect for development and testing**

### **Setup for Local Development**
```bash
# 1. Start your local EvalAI server
python manage.py runserver 0.0.0.0:8000

# 2. Configure challenge with GitHub details in EvalAI UI
# 3. Make changes - they'll sync to GitHub automatically
```

## Troubleshooting

### **Sync Not Working**
- Check that `github_repository` is set correctly in EvalAI
- Verify `github_branch` exists in your repository
- Ensure `github_token` has `repo` scope permissions
- Check EvalAI logs for sync task errors

### **Permission Issues**
- Ensure your GitHub token has `repo` scope
- Check repository access permissions
- Verify branch protection rules allow pushes

### **Common Error Messages**
- **"Repository not found"**: Check `github_repository` field
- **"Branch not found"**: Verify `github_branch` exists
- **"Permission denied"**: Check token scope and repository access

## Why One-Way Sync?

### **Design Decision**
- **Simpler architecture** - easier to maintain and debug
- **No webhook complexity** - more reliable
- **Clear data flow** - EvalAI is the source of truth
- **Version control** - all changes tracked in Git

### **Use Cases**
- **Challenge management** - hosts update challenges in EvalAI
- **Version tracking** - all changes automatically committed to Git
- **Collaboration** - team members can see changes in GitHub
- **Backup** - GitHub serves as backup of EvalAI data

## Future Enhancements

While this is a one-way sync, future versions could add:
- **Conflict detection** for manual merge scenarios
- **Sync status dashboard** in EvalAI UI
- **Advanced merge strategies** for specific fields
- **Audit logging** of all sync operations

## Summary

This implementation provides a **simple, reliable, and automatic** way to keep GitHub repositories in sync with EvalAI challenge data. By focusing on one direction, we eliminate complexity while providing immediate value to challenge hosts who want version control and backup of their challenge configurations.
