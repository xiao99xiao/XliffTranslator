import os
from dotenv import load_dotenv
import anthropic
import time
import yaml
from typing import List, Tuple, Dict
from .utils import log

class ClaudeClient:
    def __init__(self, max_retries: int = 3, retry_delay: int = 2, prompts_file: str = None):
        """
        Initialize Claude client
        Args:
            max_retries: Maximum number of retry attempts for failed translations
            retry_delay: Delay in seconds between retries
            prompts_file: Path to prompts YAML file (if None, will try 'prompts.yaml' then 'prompts.example.yaml')
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        log("Initializing Claude client", component="CLAUDE")
        load_dotenv()
        
        api_key = os.getenv('CLAUDE_API_KEY')
        if not api_key:
            log("CLAUDE_API_KEY not found", error=True, component="CLAUDE")
            raise ValueError("CLAUDE_API_KEY not found in environment or .env file")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Load prompts
        if prompts_file and os.path.exists(prompts_file):
            self.prompts_file = prompts_file
        else:
            self.prompts_file = 'prompts.yaml'
            if not os.path.exists(self.prompts_file):
                self.prompts_file = 'prompts.example.yaml'
                if not os.path.exists(self.prompts_file):
                    log("Neither prompts.yaml nor prompts.example.yaml found", error=True, component="CLAUDE")
                    raise ValueError("No prompts file found")
                log(f"Using example prompts file: {self.prompts_file}", component="CLAUDE")
            
        try:
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f)
                
            # Validate prompts structure
            required_fields = ['system_prompt', 'translation_prompt']
            for field in required_fields:
                if field not in self.prompts:
                    raise ValueError(f"Missing required field '{field}' in prompts file")
                    
            log(f"Loaded prompts from {self.prompts_file}", component="CLAUDE")
        except Exception as e:
            log(f"Failed to load prompts from {self.prompts_file}: {str(e)}", error=True, component="CLAUDE")
            raise ValueError(f"Failed to load prompts: {str(e)}")
            
        log("Claude client initialized successfully", component="CLAUDE")
    
    def translate_batch(self, texts: List[Tuple[str, str]], source_lang: str, target_lang: str, 
                       app_context: str = "", batch_size: int = 10) -> Dict[str, str]:
        """
        Translate a batch of texts with retry and split logic
        Args:
            texts: List of (id, text) tuples to translate
            source_lang: Source language code
            target_lang: Target language code
            app_context: Description of the app and its context
            batch_size: Initial batch size (will be reduced if translation fails)
        Returns: Dictionary of id -> translated_text
        """
        if not texts:
            log("No texts provided for translation", error=True, component="CLAUDE")
            raise ValueError("No texts provided for translation")
            
        translations = {}
        remaining_texts = texts
        current_batch_size = batch_size
        
        while remaining_texts:
            batch = remaining_texts[:current_batch_size]
            success = False
            
            for attempt in range(self.max_retries):
                try:
                    batch_translations = self._translate_single_batch(
                        batch, source_lang, target_lang, app_context)
                    translations.update(batch_translations)
                    remaining_texts = remaining_texts[current_batch_size:]
                    success = True
                    break
                except ValueError as e:
                    if "count mismatch" in str(e).lower() and current_batch_size > 1:
                        # Try with smaller batch size
                        log(f"Translation count mismatch, reducing batch size from {current_batch_size} to {current_batch_size//2}", 
                            component="CLAUDE")
                        current_batch_size = max(1, current_batch_size // 2)
                        break  # Break to retry with smaller batch
                    elif attempt < self.max_retries - 1:
                        log(f"Attempt {attempt + 1} failed, retrying in {self.retry_delay} seconds...", 
                            component="CLAUDE")
                        time.sleep(self.retry_delay)
                    else:
                        raise ValueError(f"Failed after {self.max_retries} attempts: {str(e)}")
                        
            if not success and current_batch_size == 1:
                # If we failed with batch size 1, something is wrong with this text
                problematic_id, problematic_text = batch[0]
                log(f"Failed to translate text: {problematic_id}", error=True, component="CLAUDE")
                log(f"Problematic text: {problematic_text}", error=True, component="CLAUDE")
                remaining_texts = remaining_texts[1:]  # Skip this text
                
        return translations
    
    def _translate_single_batch(self, texts: List[Tuple[str, str]], source_lang: str, 
                              target_lang: str, app_context: str) -> Dict[str, str]:
        """Translate a single batch of texts"""
        prompt = self._create_prompt(texts, source_lang, target_lang, app_context)
        
        log(f"Translating batch of {len(texts)} strings", component="CLAUDE")
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.2,
                system=self.prompts['system_prompt'].format(
                    target_lang=target_lang,
                    num_texts=len(texts)
                ),
                messages=[{"role": "user", "content": prompt}]
            )
            
            if hasattr(response.content, 'text'):
                translations = response.content.text.strip().split('\n')
            elif isinstance(response.content, list):
                translations = response.content[0].text.strip().split('\n')
            else:
                translations = str(response.content).strip().split('\n')
            
            # Remove any numbering that might have been added
            translations = [t.lstrip('0123456789-.). ') for t in translations]
            
            # Validate response length
            if len(translations) != len(texts):
                raise ValueError(f"Translation count mismatch: expected {len(texts)}, got {len(translations)}")
            
            return {id_: trans for (id_, _), trans in zip(texts, translations)}
            
        except Exception as e:
            log(f"Failed to translate batch: {str(e)}", error=True, component="CLAUDE")
            raise ValueError(f"Translation failed: {str(e)}")
    
    def _create_prompt(self, texts: List[Tuple[str, str]], source_lang: str, 
                      target_lang: str, app_context: str) -> str:
        """Create the translation prompt"""
        # Create numbered text list
        numbered_texts = ""
        for i, (_, text) in enumerate(texts, 1):
            numbered_texts += f"{i}. {text}\n"
            
        # Format the translation prompt template
        try:
            return self.prompts['translation_prompt'].format(
                target_lang=target_lang,
                app_context=app_context,
                numbered_texts=numbered_texts,
                num_texts=len(texts)
            )
        except KeyError as e:
            log(f"Missing key in prompt template: {str(e)}", error=True, component="CLAUDE")
            raise ValueError(f"Invalid prompt template: {str(e)}")
        except Exception as e:
            log(f"Failed to format prompt: {str(e)}", error=True, component="CLAUDE")
            raise ValueError(f"Failed to create prompt: {str(e)}") 