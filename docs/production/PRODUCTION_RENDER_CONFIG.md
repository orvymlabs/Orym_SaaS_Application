# Production Environment Variables for Render Backend

Add these to your Render backend service:

## Meta Embedded Signup Configuration

```
META_APP_ID=3862862217342382
META_CONFIG_ID=2432311603846818
META_APP_SECRET=4e8c221a2b70d959dfd452ab91a51c06
```

## Steps:

1. Go to: https://dashboard.render.com
2. Select your backend service: `orym-saas-application`
3. Click **"Environment"** in the left sidebar
4. Click **"Add Environment Variable"**
5. Add each variable above
6. Click **"Save Changes"**
7. Render will automatically redeploy (wait ~5 minutes)

## Verify it works:

After redeployment, test:
```bash
curl https://orym-saas-application.onrender.com/api/integrations/meta/config
```

Should return:
```json
{"app_id":"3862862217342382","config_id":"2432311603846818"}
```

If you get an error, the credentials aren't configured yet.
