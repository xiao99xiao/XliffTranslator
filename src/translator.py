from .xliff_parser import XliffParser
from .claude_client import ClaudeClient
from .utils import log
from typing import List, Tuple, Dict
import os
import glob

class XliffTranslator:
    def __init__(self, prompts_file: str = None):
        """
        Initialize XliffTranslator
        Args:
            prompts_file: Path to prompts YAML file (if None, will try 'prompts.yaml' then 'prompts.example.yaml')
        """
        log("Initializing XliffTranslator", component="TRANSLATOR")
        self.parser = XliffParser()
        self.claude_client = ClaudeClient(prompts_file=prompts_file)
        
    def translate_file(self, input_path: str, target_language: str, 
                      app_context: str = "", skip_translated: bool = True) -> None:
        """
        Translate XLIFF file and update it in place
        Args:
            input_path: Path to XLIFF file to translate and update
            target_language: Target language code
            app_context: Description of the app and its context
            skip_translated: Whether to skip already translated strings
        """
        log(f"Starting translation of file: {input_path}", component="TRANSLATOR")
        
        if not os.path.exists(input_path):
            log(f"Input file not found: {input_path}", error=True, component="TRANSLATOR")
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        # Create backup of original file
        backup_path = f"{input_path}.bak"
        try:
            log(f"Creating backup at: {backup_path}", component="TRANSLATOR")
            with open(input_path, 'r', encoding='utf-8') as src, \
                 open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        except Exception as e:
            log(f"Failed to create backup: {str(e)}", error=True, component="TRANSLATOR")
            raise ValueError(f"Failed to create backup: {str(e)}")
            
        try:
            # Parse input file
            log("Parsing XLIFF file...", component="TRANSLATOR")
            xliff_data, translation_pairs, existing_translations = self.parser.parse_file(
                input_path, skip_translated)
            
            if not translation_pairs and not existing_translations:
                log("No translatable strings found", error=True, component="TRANSLATOR")
                raise ValueError("No translatable strings found in the XLIFF file")
            
            if not translation_pairs:
                log("All strings already translated", component="TRANSLATOR")
                return
                
            log(f"Found {len(translation_pairs)} strings to translate", component="TRANSLATOR")
            log(f"Found {len(existing_translations)} existing translations", component="TRANSLATOR")
            
            # Add existing translations to context
            if existing_translations:
                app_context += "\n\nReference translations (DO NOT modify these, they are for context only):\n"
                for id_, trans in existing_translations.items():
                    app_context += f"- {id_}: {trans}\n"
            
            # Translate in batches
            batch_size = 10
            translations = existing_translations.copy()
            
            for i in range(0, len(translation_pairs), batch_size):
                batch = translation_pairs[i:i + batch_size]
                log(f"Translating batch {i//batch_size + 1}/{(len(translation_pairs)-1)//batch_size + 1}", 
                    component="TRANSLATOR")
                
                batch_translations = self.claude_client.translate_batch(
                    batch,
                    self.parser.source_language,
                    target_language,
                    app_context
                )
                translations.update(batch_translations)
                
                log(f"Translated {min(i + batch_size, len(translation_pairs))}/{len(translation_pairs)} strings", 
                    component="TRANSLATOR")
            
            # Update XLIFF with all translations
            log("Updating XLIFF file...", component="TRANSLATOR")
            translated_content = self.parser.update_translations(xliff_data, translations, target_language)
            
            # Update original file
            log(f"Saving changes to: {input_path}", component="TRANSLATOR")
            with open(input_path, 'w', encoding='utf-8') as f:
                f.write(translated_content)
                
            log("Translation completed successfully", component="TRANSLATOR")
            log(f"Backup saved at: {backup_path}", component="TRANSLATOR")
                
        except Exception as e:
            log(f"Translation failed: {str(e)}", error=True, component="TRANSLATOR")
            # Restore from backup if something went wrong
            try:
                log("Restoring from backup...", component="TRANSLATOR")
                with open(backup_path, 'r', encoding='utf-8') as src, \
                     open(input_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                log("Restore completed", component="TRANSLATOR")
            except Exception as restore_error:
                log(f"Failed to restore from backup: {str(restore_error)}", error=True, component="TRANSLATOR")
            raise ValueError(f"Translation failed: {str(e)}") 

    def translate_xcode_export(self, export_path: str, app_context: str = "", 
                             skip_translated: bool = True, target_languages: List[str] = None) -> Dict[str, bool]:
        """
        Translate all XLIFF files in an Xcode export folder
        Args:
            export_path: Path to the Xcode export folder
            app_context: Description of the app and its context
            skip_translated: Whether to skip already translated strings
            target_languages: List of language codes to process (None for all)
        Returns:
            Dictionary of language code -> success status
        """
        log(f"Processing Xcode export folder: {export_path}", component="TRANSLATOR")
        
        if not os.path.isdir(export_path):
            raise ValueError(f"Not a directory: {export_path}")
            
        # Find all .xcloc folders except en.xcloc
        xcloc_pattern = os.path.join(export_path, "*.xcloc")
        xcloc_folders = glob.glob(xcloc_pattern)
        
        if not xcloc_folders:
            raise ValueError(f"No .xcloc folders found in {export_path}")
            
        results = {}
        
        for xcloc_folder in xcloc_folders:
            lang_code = os.path.basename(xcloc_folder).replace('.xcloc', '')
            
            # Skip English source
            if lang_code.lower() == 'en':
                log(f"Skipping English source folder: {xcloc_folder}", component="TRANSLATOR")
                continue
                
            # Skip if not in target languages
            if target_languages and lang_code not in target_languages:
                log(f"Skipping non-target language: {lang_code}", component="TRANSLATOR")
                continue
                
            xliff_path = os.path.join(xcloc_folder, "Localized Contents", f"{lang_code}.xliff")
            
            if not os.path.exists(xliff_path):
                log(f"XLIFF file not found for {lang_code}: {xliff_path}", error=True, component="TRANSLATOR")
                results[lang_code] = False
                continue
                
            log(f"Processing {lang_code} translation: {xliff_path}", component="TRANSLATOR")
            
            try:
                self.translate_file(
                    input_path=xliff_path,
                    target_language=lang_code,
                    app_context=app_context,
                    skip_translated=skip_translated
                )
                results[lang_code] = True
                log(f"Successfully translated {lang_code}", component="TRANSLATOR")
                
            except Exception as e:
                log(f"Failed to translate {lang_code}: {str(e)}", error=True, component="TRANSLATOR")
                results[lang_code] = False
        
        # Print summary
        self._print_translation_summary(results)
        return results
    
    def _print_translation_summary(self, results: Dict[str, bool]):
        """Print translation results summary"""
        log("\nTranslation Summary:", component="TRANSLATOR")
        successful = [lang for lang, success in results.items() if success]
        failed = [lang for lang, success in results.items() if not success]
        
        if successful:
            log("Successfully translated:", component="TRANSLATOR")
            for lang in successful:
                log(f"  - {lang}", component="TRANSLATOR")
        
        if failed:
            log("Failed to translate:", component="TRANSLATOR")
            for lang in failed:
                log(f"  - {lang}", component="TRANSLATOR") 