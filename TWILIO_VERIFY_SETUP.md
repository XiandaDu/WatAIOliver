# Twilio Verify Setup

## Environment Variables Required

Add these environment variables to your `backend/.env` file:

```bash
# Twilio Verify Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_VERIFY_SERVICE_SID=your_twilio_verify_service_sid_here
```

## How to Get Twilio Verify Credentials

1. **Sign up for Twilio** (if you haven't already):
   - Go to [https://www.twilio.com](https://www.twilio.com)
   - Sign up for a free account

2. **Get Account Credentials**:
   - Go to Console Dashboard
   - Find your Account SID and Auth Token
   - Copy these values

3. **Create a Verify Service**:
   - Go to Verify → Services in the Twilio Console
   - Click "Create Service"
   - Give it a name like "WatAI Oliver Email Verification"
   - Copy the Service SID

4. **Update Environment Variables**:
   - Add all three values to your `backend/.env` file
   - Restart your backend server

## How It Works

- **With Twilio Verify**: Sends actual verification emails via Twilio
- **Without Twilio**: Falls back to console display (for development)
- **Automatic Fallback**: If Twilio fails, uses manual verification


