#!/bin/bash
# run_src_migration.sh

mkdir -p src/foundry
touch src/foundry/__init__.py

# Move directories
for dir in config core data_pipeline ai_engine api database utils; do
    if [ -d "$dir" ]; then
        mv "$dir" src/foundry/
    fi
done

echo "✅ Moved all packages to src/foundry/"
echo "⚠️  Now update your imports!"