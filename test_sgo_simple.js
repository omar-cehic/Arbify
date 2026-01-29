// test_sgo_simple.js - Simple JavaScript test for SGO API integration
// Run with: node test_sgo_simple.js

const https = require('https');

const SGO_API_KEY = process.env.SGO_API_KEY;
const SGO_BASE_URL = "https://api.sportsgameodds.com/v2";

console.log("🧪 Testing SportsGameOdds API Integration");
console.log("=" + "=".repeat(49));

// Test function to make API calls
function testSGOAPI() {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'api.sportsgameodds.com',
            port: 443,
            path: '/v2/sports',
            method: 'GET',
            headers: {
                'X-API-Key': SGO_API_KEY,
                'User-Agent': 'ArbitrageBetting/1.0'
            }
        };

        console.log("\n1️⃣ Testing API Connection...");
        console.log("🌐 Making request to:", `${SGO_BASE_URL}/sports`);
        console.log("🔑 Using API Key:", SGO_API_KEY.substring(0, 8) + "...");

        const req = https.request(options, (res) => {
            let data = '';

            res.on('data', (chunk) => {
                data += chunk;
            });

            res.on('end', () => {
                console.log("📡 Response Status:", res.statusCode);
                console.log("📦 Response Headers:", res.headers);

                if (res.statusCode === 200) {
                    try {
                        const jsonData = JSON.parse(data);
                        console.log("✅ SGO API connection successful!");
                        console.log("📊 Found", jsonData.length || 0, "sports available");

                        if (jsonData.length > 0) {
                            console.log("📋 Sample sports:", jsonData.slice(0, 5).map(s => s.name || s.title || 'Unknown').join(', '));
                        }

                        resolve(jsonData);
                    } catch (parseError) {
                        console.log("❌ JSON Parse Error:", parseError.message);
                        console.log("📄 Raw Response:", data.substring(0, 200) + "...");
                        reject(parseError);
                    }
                } else {
                    console.log("❌ SGO API Error - Status:", res.statusCode);
                    console.log("📄 Response Body:", data);
                    reject(new Error(`HTTP ${res.statusCode}: ${data}`));
                }
            });
        });

        req.on('error', (error) => {
            console.log("❌ Request Error:", error.message);
            reject(error);
        });

        req.setTimeout(10000, () => {
            console.log("❌ Request Timeout");
            req.destroy();
            reject(new Error('Request timeout'));
        });

        req.end();
    });
}

// Run the test
testSGOAPI()
    .then((data) => {
        console.log("\n🎉 SGO Integration Test Complete!");
        console.log("✅ API Key is valid and working");
        console.log("✅ Connection established successfully");
        console.log("✅ Ready to integrate with your arbitrage system");

        console.log("\n📋 Next Steps:");
        console.log("1. Start your backend server: python main.py");
        console.log("2. Start your frontend: cd frontend && npm start");
        console.log("3. Visit /arbitrage page to see SGO data");
        console.log("4. Check /api/arbitrage/sgo endpoint");
    })
    .catch((error) => {
        console.log("\n❌ SGO Integration Test Failed!");
        console.log("Error:", error.message);

        if (error.message.includes('401') || error.message.includes('403')) {
            console.log("\n🔑 API Key Issue:");
            console.log("- Check if API key is correct");
            console.log("- Verify account status with SportsGameOdds");
            console.log("- Check if key has required permissions");
        } else if (error.message.includes('timeout')) {
            console.log("\n🌐 Network Issue:");
            console.log("- Check internet connection");
            console.log("- Try again in a few minutes");
            console.log("- Check if firewall is blocking requests");
        } else {
            console.log("\n🔧 Other Issue:");
            console.log("- Check SGO API documentation");
            console.log("- Contact SGO support if needed");
        }
    });
