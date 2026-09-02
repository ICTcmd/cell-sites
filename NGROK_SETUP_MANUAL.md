# 🌐 ngrok Manual Setup Guide

Your backend is running perfectly on `localhost:8000`! ✅

Now we need to expose it to the internet so your Vercel frontend can connect.

---

## 🚨 Current Issue

ngrok is stuck on "connecting" - this could be:
- Firewall blocking ngrok
- Antivirus blocking the connection
- Network/proxy issues

---

## ✅ Manual Setup Steps

### Step 1: Open a NEW Command Prompt or PowerShell

Press `Win + R`, type `cmd`, press Enter

### Step 2: Run ngrok manually

```bash
ngrok http 8000
```

### Step 3: Look for the Forwarding URL

You should see output like:

```
Session Status                online
Version                       3.39.11
Region                        United States (us)
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**Copy this URL**: `https://abc123.ngrok-free.app`

---

## 📋 What to Do Next

Once you have the ngrok URL:

### 1. Test the Backend

Open browser and visit:
```
https://YOUR-NGROK-URL/health
```

You should see:
```json
{"status":"healthy","timestamp":"..."}
```

### 2. Update Vercel Environment Variable

1. Go to: https://vercel.com/dashboard
2. Select project: **cell-sites**
3. Go to: **Settings** → **Environment Variables**
4. Find: `NEXT_PUBLIC_API_URL`
5. Update to: `https://YOUR-NGROK-URL/api/v1`
   - Example: `https://abc123.ngrok-free.app/api/v1`
6. Click **Save**

### 3. Redeploy Frontend

1. Go to **Deployments** tab
2. Click **Redeploy** on latest deployment
3. Wait ~30 seconds

### 4. Test Everything

Visit: https://cell-sites.vercel.app

The map should load and connect to your local backend! 🎉

---

## 🔥 Troubleshooting

### ngrok still won't connect?

**Check your firewall:**

1. Open **Windows Defender Firewall**
2. Click **Allow an app through firewall**
3. Look for **ngrok** - make sure both Private and Public are checked
4. If not listed, click **Allow another app** and browse to ngrok

**Try different port:**
```bash
# Stop the current ngrok (Ctrl+C)
# Try with different port forwarding
ngrok http 8000 --region us
```

**Check if port 8000 is accessible:**
```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy",...}`

---

## 📱 Alternative: Use Local IP (For Android Testing Only)

If ngrok doesn't work, you can test the Android app using your computer's local IP:

### Find your local IP:
```bash
ipconfig
```

Look for **IPv4 Address** (something like `192.168.1.100`)

### Update Android app:
```kotlin
private val apiBaseUrl: String = "http://192.168.1.100:8000/api/v1"
```

**NOTE**: This only works when phone and computer are on the same WiFi network!

---

## ⚠️ Important Notes

### Keep ngrok running!
- Don't close the terminal window where ngrok is running
- The URL will stop working if you close it

### Free tier limitations:
- Random URL each time you restart
- If ngrok restarts, update Vercel with new URL
- For permanent URL, upgrade to paid plan ($8/month)

---

## 🎯 Current Status

✅ Docker backend running on `localhost:8000`  
✅ PostgreSQL database running  
✅ Vercel frontend deployed at `https://cell-sites.vercel.app`  
⏳ Need ngrok tunnel to connect them  

---

## 🆘 Need Help?

1. **Try running ngrok manually** in a new terminal
2. **Check Windows Firewall** settings
3. **Temporarily disable antivirus** and try again
4. **Screenshot the ngrok output** if you see errors

Once you get the ngrok URL, send it and we'll complete the setup! 🚀
