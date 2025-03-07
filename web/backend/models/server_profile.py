#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('server_profile')

class ServerProfile:
    """Class to manage server profiles"""
    def __init__(self, profile_file=None):
        # Use the provided profile file or use the default in config directory
        if profile_file:
            self.profile_file = profile_file
        else:
            # Use the profiles.json file in the config directory
            self.profile_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'profiles.json')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.profile_file), exist_ok=True)
        
        # Load profiles
        self.profiles = self._load_profiles()
    
    def _load_profiles(self):
        """Load profiles from JSON file"""
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    logger.info(f"Loading profiles from {self.profile_file}")
                    content = f.read().strip()
                    if not content:
                        logger.warning("Profile file is empty")
                        return {}
                    return json.loads(content)
            logger.info("Profile file not found. Creating new.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding profile file: {str(e)}")
            # Backup corrupted file
            if os.path.exists(self.profile_file):
                backup_file = f"{self.profile_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                try:
                    os.rename(self.profile_file, backup_file)
                    logger.info(f"Backup of corrupted file created: {backup_file}")
                except Exception as be:
                    logger.error(f"Error creating backup: {str(be)}")
            return {}
        except Exception as e:
            logger.error(f"Error loading profiles: {str(e)}")
            return {}
    
    def _save_profiles(self):
        """Save profiles to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.profile_file), exist_ok=True)
            
            # Validate data before saving
            if not isinstance(self.profiles, dict):
                logger.error(f"Invalid profile data: {type(self.profiles)}")
                return False
                
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
            logger.info(f"Profiles saved to {self.profile_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving profiles: {str(e)}")
            return False
            
    def get_profile_names(self):
        """Returns a list of registered profile names"""
        return list(self.profiles.keys())
        
    def get_profile(self, name):
        """Returns a specific profile by name"""
        return self.profiles.get(name, {})
        
    def add_profile(self, name, host, port, username, password, key_path, use_key):
        """Adds or updates a profile in the system"""
        # Validation checks
        if not self._validate_profile_data(name, host, username, password, key_path, use_key):
            return False
            
        # Sanitize values
        name = name.strip()
        host = host.strip()
        port = port.strip() if port else ""  # Allow empty port
        username = username.strip()
        
        # Store profile
        self.profiles[name] = {
            "host": host,
            "port": port,
            "username": username,
            "password": password if not use_key else "",
            "key_path": key_path if use_key else "",
            "use_key": use_key
        }
        
        result = self._save_profiles()
        if result:
            logger.info(f"Profile '{name}' added successfully")
        return result
    
    def _validate_profile_data(self, name, host, username, password, key_path, use_key):
        """Validates profile data before saving"""
        if not name or not host or not username:
            logger.warning("Attempt to add profile with missing required fields")
            return False
            
        # Check authentication method
        if use_key:
            if not key_path:
                logger.warning(f"Key path not provided for key authentication")
                return False
        else:
            if not password:
                logger.warning("Password not provided for password authentication")
                return False
                
        return True
        
    def update_profile(self, name, host, port, username, password, key_path, use_key):
        """Updates an existing profile"""
        if name in self.profiles:
            logger.info(f"Updating profile '{name}'")
            return self.add_profile(name, host, port, username, password, key_path, use_key)
        logger.warning(f"Attempt to update non-existent profile: '{name}'")
        return False
        
    def delete_profile(self, name):
        """Removes a profile"""
        if name in self.profiles:
            del self.profiles[name]
            logger.info(f"Profile '{name}' deleted")
            return self._save_profiles()
        logger.warning(f"Attempt to delete non-existent profile: '{name}'")
        return False