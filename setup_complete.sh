#!/bin/bash
# Complete setup script

echo "Setting up complete Rakhine lexicon repository..."

# Run initialization
./init_project.sh

# Make scripts executable
chmod +x scripts/*.py
chmod +x scripts/analysis/*.py

echo ""
echo "✅ Setup complete! Your repository is ready for:"
echo ""
echo "1. Adding lexicon entries to data/lexicon.json"
echo "2. Recording audio pronunciations"
echo "3. Building language corpora"
echo "4. Training AI models"
echo ""
echo "See README.md for detailed instructions."