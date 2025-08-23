# Bi-directional Sync with EvalAI

This repository now supports **bi-directional synchronization** between GitHub and EvalAI using the existing `AUTH_TOKEN` repository secret.

## How It Works

### **Before (One-way sync):**
- ✅ EvalAI → GitHub: Automatic (when you update challenges in EvalAI)
- ❌ GitHub → EvalAI: Manual (you had to manually trigger sync)

### **After (Bi-directional sync):**
- ✅ EvalAI → GitHub: Automatic (when you update challenges in EvalAI)
- ✅ GitHub → EvalAI: Automatic (when you push changes to GitHub)

## Setup Requirements

### **1. Repository Secret (Already configured)**
- `AUTH_TOKEN`: Your GitHub personal access token
- **Scope**: Must have `repo` permissions to manage webhooks
- **Location**: Repository Settings → Secrets and variables → Actions

### **2. Host Configuration**
```json
{
    "token": "<evalai_user_auth_token>",
    "team_pk": "<host_team_pk>",
    "evalai_host_url": "<evalai_host_url>"
}
```

## How the Sync Works

### **GitHub → EvalAI (Automatic via Webhook)**
1. You push changes to GitHub repository
2. GitHub automatically sends a webhook to EvalAI
3. EvalAI receives the webhook and identifies affected challenges
4. EvalAI pulls the updated `challenge_config.yaml` from GitHub
5. Challenge is updated in EvalAI database
6. `last_github_sync` timestamp is updated

### **EvalAI → GitHub (Existing functionality)**
1. You update a challenge in EvalAI
2. EvalAI automatically pushes changes to GitHub repository
3. GitHub repository is updated with new challenge configuration

## Webhook Configuration

The script automatically sets up the required GitHub webhook:

- **URL**: `https://your-evalai-domain.com/api/v1/challenges/github/webhook/`
- **Events**: `push` events only
- **Content Type**: `application/json`
- **Secret**: None (for MVP simplicity)

## What Gets Synced

### **From GitHub to EvalAI:**
- `title`
- `description`
- `evaluation_details`
- Basic challenge metadata

### **From EvalAI to GitHub:**
- All challenge configuration files
- Evaluation scripts
- Challenge metadata

## Usage

### **Automatic Setup**
When you run the challenge processing script:
1. It automatically detects your `AUTH_TOKEN`
2. Sets up the GitHub webhook for bi-directional sync
3. Configures the sync endpoints

### **Manual Webhook Setup (if automatic fails)**
If automatic webhook setup fails:
1. Go to your GitHub repository
2. Settings → Webhooks → Add webhook
3. **Payload URL**: `https://your-evalai-domain.com/api/v1/challenges/github/webhook/`
4. **Content type**: `application/json`
5. **Events**: Select "Just the push event"
6. **Active**: ✓

## Troubleshooting

### **Webhook Setup Fails**
- Ensure your `AUTH_TOKEN` has `repo` scope permissions
- Check that your EvalAI server is publicly accessible
- Verify the webhook URL is correct

### **Sync Not Working**
- Check webhook delivery status in GitHub repository settings
- Verify EvalAI server logs for webhook reception
- Ensure `challenge_config.yaml` is in the repository root

### **Localhost Development**
- Bi-directional sync is skipped for localhost servers
- Webhooks require publicly accessible endpoints
- Use self-hosted runners for local development

## Benefits

1. **Real-time Updates**: Changes propagate automatically in both directions
2. **No Manual Intervention**: Set it up once, works automatically
3. **Consistent State**: GitHub and EvalAI stay in sync
4. **Simple Configuration**: Uses existing `AUTH_TOKEN` secret

## Security Notes

- **MVP Implementation**: No webhook signature verification
- **Production Ready**: Can be enhanced with signature verification later
- **Token Permissions**: `AUTH_TOKEN` needs `repo` scope for webhook management

## Future Enhancements

- Webhook signature verification
- Conflict detection and resolution
- Sync status dashboard
- Advanced merge strategies
- Audit logging
