# Gmail OAuth Integration - Environment Variables

This document describes the environment variables required for Gmail OAuth integration (Story 6.1).

## Required Environment Variables

Add these to your `.env` file in the project root:

```bash
# Google OAuth Credentials
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
GOOGLE_OAUTH_REDIRECT=http://localhost:3000/api/integrations/gmail/callback

# Token Encryption Key (32-byte base64-encoded)
EMAIL_TOKEN_ENCRYPTION_KEY=<32-byte-base64-key>
```

## Setup Instructions

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: "Web application"
6. Authorized redirect URIs:
   - Development: `http://localhost:3000/api/integrations/gmail/callback`
   - Production: `https://your-domain.com/api/integrations/gmail/callback`
7. Copy the Client ID and Client Secret

### 2. Generate Encryption Key

Run this command to generate a secure 32-byte encryption key:

```bash
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

### 3. Add to .env File

```bash
# Example .env
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxx
GOOGLE_OAUTH_REDIRECT=http://localhost:3000/api/integrations/gmail/callback
EMAIL_TOKEN_ENCRYPTION_KEY=abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx==
```

## Security Notes

- **Never commit** `.env` to version control
- **Rotate encryption keys** periodically in production
- **Use HTTPS** for all OAuth redirects in production
- **Store encryption keys** in a secure secrets manager (e.g., AWS Secrets Manager, Azure Key Vault) for production

## Testing

To test the integration locally:

1. Set up environment variables as described above
2. Run the API server: `uvicorn app.main:app --reload`
3. Run the frontend: `npm run dev`
4. Navigate to `http://localhost:3000/dashboard/integrations`
5. Click "Connect Gmail" and complete the OAuth flow

## Troubleshooting

### "GOOGLE_CLIENT_ID not configured"
- Ensure `GOOGLE_CLIENT_ID` is set in your `.env` file
- Restart the API server after adding environment variables

### "EMAIL_TOKEN_ENCRYPTION_KEY not set"
- Generate a new key using the command above
- Add it to your `.env` file
- Restart the API server

### OAuth redirect mismatch
- Ensure the redirect URI in your `.env` matches exactly what's configured in Google Cloud Console
- Include the protocol (`http://` or `https://`)
- Check for trailing slashes

## Production Deployment

For production environments:

1. Use environment-specific OAuth credentials
2. Store secrets in a secrets manager
3. Use HTTPS for all OAuth flows
4. Set `GOOGLE_OAUTH_REDIRECT` to your production domain
5. Enable Google's OAuth consent screen verification
