#!/bin/zsh

# Directory containing .xcloc files
LOCALIZATIONS_DIR="path/to/your/localizations/folder"

# Project path (relative to this script or absolute path)
PROJECT_PATH="path/to/your/Project.xcodeproj"

echo "Starting localization import..."
echo "Localizations directory: $LOCALIZATIONS_DIR"
echo "Project path: $PROJECT_PATH"
echo "----------------------------------------"

# Find all .xcloc files (excluding en.xcloc) and process them one by one
find "$LOCALIZATIONS_DIR" -name "*.xcloc" | grep -v "en.xcloc" | while read -r xcloc_file; do
    echo "Importing localization: $xcloc_file"
    xcodebuild -importLocalizations -project "$PROJECT_PATH" -localizationPath "$xcloc_file"
    
    # Check if the command was successful
    if [ $? -eq 0 ]; then
        echo "Successfully imported: $xcloc_file"
    else
        echo "Failed to import: $xcloc_file"
        echo "Please check if the project path is correct and you have the necessary permissions."
    fi
    
    echo "----------------------------------------"
done

echo "All localizations have been processed." 