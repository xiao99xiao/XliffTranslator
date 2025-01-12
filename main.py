#!/usr/bin/env python3

import argparse
import os
import sys
import yaml
from src.translator import XliffTranslator

def load_app_context(context_file: str = "app_context.yaml") -> str:
    """Load app context from YAML file"""
    if not os.path.exists(context_file):
        print(f"Warning: App context file '{context_file}' not found")
        return ""
        
    try:
        with open(context_file, 'r', encoding='utf-8') as f:
            context_data = yaml.safe_load(f)
            
        # Validate required fields
        required_fields = ['app_description', 'preserve_names', 'terminology', 'style_guide']
        for field in required_fields:
            if field not in context_data:
                raise ValueError(f"Missing required field '{field}' in app context file")
                
        # Format context string
        context = context_data['app_description'] + "\n\nKey Terminology:\n"
        for term in context_data.get('terminology', []):
            if 'term' not in term or 'description' not in term:
                raise ValueError("Each terminology entry must have 'term' and 'description' fields")
            context += f"- {term['term']}: {term['description']}\n"
        
        context += "\nStyle Guide:\n"
        for key, value in context_data.get('style_guide', {}).items():
            context += f"- {key}: {value}\n"
            
        return context
    except Exception as e:
        print(f"Warning: Could not load app context file: {e}")
        return ""

def parse_arguments():
    parser = argparse.ArgumentParser(description='Translate XLIFF files using Claude AI')
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i', help='Single XLIFF file to translate')
    input_group.add_argument('--folder', '-f', help='Xcode export folder containing .xcloc folders')
    
    parser.add_argument('--target-language', '-t', help='Target language code (required for single file)',
                       required=False)
    parser.add_argument('--languages', '-l', help='Comma-separated list of language codes to process (folder mode only)',
                       type=str)
    parser.add_argument('--context-file', '-c', default='app_context.yaml',
                       help='Path to app context YAML file')
    parser.add_argument('--prompts-file', '-p', help='Path to prompts YAML file')
    parser.add_argument('--translate-all', '-a', action='store_true',
                       help='Translate all strings, including already translated ones')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.input and not args.target_language:
        parser.error("--target-language is required when using --input")
    
    if args.languages and not args.folder:
        parser.error("--languages can only be used with --folder")
        
    if args.prompts_file and not os.path.exists(args.prompts_file):
        parser.error(f"Prompts file not found: {args.prompts_file}")
    
    return args

def main():
    args = parse_arguments()
    
    try:
        app_context = load_app_context(args.context_file)
        translator = XliffTranslator(prompts_file=args.prompts_file)
        
        if args.input:
            # Single file mode
            if not os.path.exists(args.input):
                print(f"Error: Input file '{args.input}' does not exist")
                sys.exit(1)
                
            translator.translate_file(
                input_path=args.input,
                target_language=args.target_language,
                app_context=app_context,
                skip_translated=not args.translate_all
            )
            print(f"Translation completed successfully. Original file updated: {args.input}")
            print(f"Backup saved at: {args.input}.bak")
            
        else:
            # Folder mode
            if not os.path.exists(args.folder):
                print(f"Error: Folder '{args.folder}' does not exist")
                sys.exit(1)
            
            # Parse language codes if provided
            target_languages = None
            if args.languages:
                target_languages = [lang.strip() for lang in args.languages.split(',')]
                print(f"Processing specified languages: {', '.join(target_languages)}")
                
            results = translator.translate_xcode_export(
                export_path=args.folder,
                app_context=app_context,
                skip_translated=not args.translate_all,
                target_languages=target_languages
            )
            
            # Results already logged by the translator
            if not any(results.values()):
                sys.exit(1)  # Exit with error if all translations failed
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 