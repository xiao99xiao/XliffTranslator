import xmltodict
from typing import Dict, List, Tuple
from .utils import log

class XliffParser:
    def __init__(self):
        self.source_language = None
        self.target_language = None
        log("XLIFF Parser initialized", component="PARSER")
    
    def parse_file(self, file_path: str, skip_translated: bool = True) -> Tuple[Dict, List[Tuple[str, str]], Dict[str, str]]:
        """
        Parse XLIFF file and extract translatable strings
        Args:
            file_path: Path to XLIFF file
            skip_translated: Whether to skip already translated strings
        Returns: 
            Tuple of (xliff_data, translation_pairs, existing_translations)
            - xliff_data: Full XLIFF structure
            - translation_pairs: List of (id, source) tuples needing translation
            - existing_translations: Dict of id -> target for already translated strings
        """
        log(f"Parsing XLIFF file: {file_path}", component="PARSER")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        xliff_data = xmltodict.parse(content)
        log("XLIFF file parsed successfully", component="PARSER")
        
        # Debug the structure
        log(f"XLIFF data structure: {xliff_data.keys()}", component="PARSER")
        if 'xliff' in xliff_data:
            log(f"XLIFF content: {xliff_data['xliff'].keys()}", component="PARSER")
            if 'file' in xliff_data['xliff']:
                log(f"File content type: {type(xliff_data['xliff']['file'])}", component="PARSER")
                if isinstance(xliff_data['xliff']['file'], list):
                    log(f"Multiple files found: {len(xliff_data['xliff']['file'])}", component="PARSER")
                    self.source_language = xliff_data['xliff']['file'][0].get('@source-language')
                else:
                    log("Single file found", component="PARSER")
                    self.source_language = xliff_data['xliff']['file'].get('@source-language')
            else:
                raise ValueError("No 'file' element found in XLIFF")
        else:
            raise ValueError("Invalid XLIFF structure: no 'xliff' root element")
        
        if not self.source_language:
            raise ValueError("Source language not found in XLIFF file")
            
        log(f"Source language: {self.source_language}", component="PARSER")
        
        # Get all trans-units
        translation_pairs = []
        existing_translations = {}
        files = xliff_data['xliff']['file']
        
        if isinstance(files, list):
            log(f"Processing {len(files)} XLIFF files", component="PARSER")
            for file in files:
                self._extract_trans_units(file, translation_pairs, existing_translations, skip_translated)
        else:
            log("Processing single XLIFF file", component="PARSER")
            self._extract_trans_units(files, translation_pairs, existing_translations, skip_translated)
            
        log(f"Found {len(translation_pairs)} strings needing translation", component="PARSER")
        log(f"Found {len(existing_translations)} existing translations", component="PARSER")
        return xliff_data, translation_pairs, existing_translations
    
    def _extract_trans_units(self, file_data: Dict, translation_pairs: List, existing_translations: Dict, skip_translated: bool):
        """Extract source and target pairs from trans-units"""
        body = file_data.get('body', {})
        trans_units = body.get('trans-unit', [])
        
        if not isinstance(trans_units, list):
            trans_units = [trans_units]
            
        for unit in trans_units:
            if isinstance(unit, dict):
                unit_id = unit.get('@id', '')
                source = unit.get('source', '')
                target = unit.get('target', '')
                
                if source:
                    if target and skip_translated:
                        # Store existing translation
                        existing_translations[unit_id] = target
                        log(f"Skipping already translated string: {unit_id}", component="PARSER")
                    else:
                        # Add to pairs needing translation
                        translation_pairs.append((unit_id, source))
    
    def update_translations(self, xliff_data: Dict, translations: Dict[str, str], target_language: str) -> str:
        """Update XLIFF data with translations and return as string"""
        log("Starting to update translations in XLIFF", component="PARSER")
        
        # Set target language
        files = xliff_data['xliff']['file']
        if isinstance(files, list):
            log(f"Updating {len(files)} files", component="PARSER")
            for file in files:
                if isinstance(file, dict):
                    file['@target-language'] = target_language
                    self._update_trans_units(file, translations)
        else:
            log("Updating single file", component="PARSER")
            xliff_data['xliff']['file']['@target-language'] = target_language
            self._update_trans_units(xliff_data['xliff']['file'], translations)
        
        log("Translations updated successfully", component="PARSER")
        return xmltodict.unparse(xliff_data, pretty=True)
    
    def _update_trans_units(self, file_data: Dict, translations: Dict[str, str]):
        """Update trans-units with translations"""
        log("Updating trans-units", component="PARSER")
        
        if not isinstance(file_data, dict):
            log(f"Invalid file_data type: {type(file_data)}", error=True, component="PARSER")
            return
            
        body = file_data.get('body', {})
        if not body:
            log("No body found in file data", error=True, component="PARSER")
            return
            
        trans_units = body.get('trans-unit', [])
        if not trans_units:
            log("No trans-units found", error=True, component="PARSER")
            return
            
        if not isinstance(trans_units, list):
            trans_units = [trans_units]
        
        updated_count = 0
        for unit in trans_units:
            if isinstance(unit, dict):
                unit_id = unit.get('@id', '')
                if unit_id in translations:
                    unit['target'] = translations[unit_id]
                    updated_count += 1
                    
        log(f"Updated {updated_count} translations", component="PARSER") 