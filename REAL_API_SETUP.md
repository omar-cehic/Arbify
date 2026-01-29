# 🚀 Real API Integration Setup Guide

## Step 1: Get Your API Key

1. **Visit:** https://the-odds-api.com/
2. **Click:** "Get a Free API Key" 
3. **Sign up** with your email
4. **Copy your API key** (you'll need this)

## Step 2: Add API Key to Environment

### For Local Development:
Add this line to your `.env` file:
```
ODDS_API_KEY=your_actual_api_key_here
```

### For Railway Production:
1. Go to your Railway project dashboard
2. Click on **Variables** tab  
3. Add new variable:
   - **Name:** `ODDS_API_KEY`
   - **Value:** `your_actual_api_key_here`

## Step 3: Switch from Mock to Real Data

### Current Status:
- **DEV_MODE = True** → Uses mock data
- **DEV_MODE = False** → Uses real API data

### To Test Real API:
1. Temporarily set `DEV_MODE = False` in `config.py`
2. Restart your local server
3. Test the `/api/arbitrage` endpoint
4. Check logs for API response

### For Production:
- Railway automatically sets `DEV_MODE = False`
- Real API will be used automatically

## Step 4: Monitor API Usage

### Free Plan Limits:
- **500 credits/month**
- Perfect for development and testing

### Usage Monitoring:
1. Check your dashboard at: https://the-odds-api.com/account
2. Monitor credit usage
3. Upgrade when needed

## Step 5: API Endpoints Available

### Sports Coverage:
- **Soccer:** EPL, La Liga, Bundesliga, Serie A
- **American Football:** NFL, NCAA
- **Basketball:** NBA, NCAA
- **Baseball:** MLB
- **Tennis:** ATP, WTA
- **Hockey:** NHL

### Markets:
- **h2h:** Head to Head (Moneyline)
- **spreads:** Point Spreads
- **totals:** Over/Under

## Step 6: Testing the Integration

### Test Commands:
```bash
# Test odds endpoint
curl "http://localhost:8000/api/odds"

# Test arbitrage detection  
curl "http://localhost:8000/api/arbitrage" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Expected Response:
```json
{
  "arbitrage_opportunities": [
    {
      "match": {
        "home_team": "Arsenal",
        "away_team": "Chelsea"
      },
      "sport_title": "English Premier League",
      "profit_percentage": 2.15,
      "best_odds": {
        "Arsenal": {"bookmaker": "Bet365", "odds": 2.1},
        "Chelsea": {"bookmaker": "DraftKings", "odds": 2.2}
      }
    }
  ],
  "user_tier": "premium",
  "data_source": "real_api"
}
```

## Step 7: Polling Intervals Optimized

### New Intervals:
- **Premium/Trial:** 40 seconds (matches API live updates)
- **Basic:** 60 seconds (matches API pre-match updates)  
- **Free:** 120 seconds (conservative)

## Step 8: Error Handling

### Common Issues:
1. **401 Unauthorized:** Invalid API key
2. **429 Rate Limited:** Too many requests
3. **500 Server Error:** API endpoint issues

### Monitoring:
- Check server logs for API errors
- Monitor credit usage
- Set up alerts for failures

## Step 9: Upgrade Path

### When to Upgrade:
- **20K Plan ($30/month):** 10-20 active users
- **100K Plan ($59/month):** 50+ active users  
- **5M Plan ($119/month):** 100+ active users

## 🎯 Ready to Launch!

Once you have real data flowing:
1. ✅ Test arbitrage detection
2. ✅ Verify user tier restrictions  
3. ✅ Check email notifications
4. ✅ Test browser notifications
5. ✅ Monitor API usage

## 🔧 Development Tips

### Testing with Free Credits:
- Use selective sports for testing
- Test during off-peak hours
- Monitor credit usage closely
- Switch back to mock data when developing UI

### Production Best Practices:
- Cache API responses for 30-60 seconds
- Implement exponential backoff for errors
- Monitor API health
- Set up usage alerts
