#!/bin/bash
echo "🧹 Cleaning Next.js cache..."
rm -rf .next
rm -rf node_modules
echo "✅ Cache cleared!"
echo ""
echo "📦 Reinstalling dependencies..."
npm install
echo ""
echo "✅ Ready! Now run: npm run dev"
