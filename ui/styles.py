#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import platform
import os

class ResponsiveUI:
    """Class to handle responsive UI elements and styling for the application"""
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Track window size changes
        self.current_width = root.winfo_width()
        self.current_height = root.winfo_height()
        
        # Define breakpoints for responsive design
        self.breakpoints = {
            'xsmall': 480,
            'small': 768,
            'medium': 992,
            'large': 1200,
            'xlarge': 1600
        }
        
        # Define color palette - Modern, professional color scheme with better contrast
        self.colors = {
            'bg_primary': '#f8f9fa',      # Lighter background
            'bg_secondary': '#ffffff',    # White for cards/panels
            'bg_tertiary': '#e9ecef',     # Slightly darker for contrast areas
            'fg_primary': '#212529',      # Dark text for good contrast
            'fg_secondary': '#495057',    # Secondary text
            'fg_muted': '#6c757d',        # Muted text for less important elements
            'accent': '#0d6efd',          # Primary blue accent
            'accent_hover': '#0b5ed7',    # Darker blue for hover states
            'success': '#198754',         # Green for success states
            'success_hover': '#157347',   # Darker green for hover
            'warning': '#ffc107',         # Yellow for warnings
            'warning_hover': '#e0a800',   # Darker yellow for hover
            'danger': '#dc3545',          # Red for danger/errors
            'danger_hover': '#bb2d3b',    # Darker red for hover
            'info': '#0dcaf0',            # Light blue for info
            'info_hover': '#0aa1c0',      # Darker info for hover
            'border': '#dee2e6',          # Light gray border
            'disabled': '#e9ecef'         # Disabled state background
        }
        
        # Initialize styles
        self._init_styles()
        
        # Bind resize event
        root.bind('<Configure>', self._on_resize)
    
    def _init_styles(self):
        """Initialize custom styles for the application"""
        # Configure the main theme
        self.style.configure('TFrame', background=self.colors['bg_primary'])
        self.style.configure('TNotebook', background=self.colors['bg_primary'])
        self.style.configure('TNotebook.Tab', 
                            padding=[10, 5], 
                            font=('Segoe UI', 10, 'bold'), 
                            background=self.colors['bg_tertiary'], 
                            foreground=self.colors['fg_primary'],
                            borderwidth=1,
                            relief='flat')
        self.style.map('TNotebook.Tab', 
                      background=[('selected', self.colors['accent'])], 
                      foreground=[('selected', self.colors['fg_primary'])],
                      relief=[('selected', 'sunken')])
        
        # Configure button styles with hover effects
        self.style.configure('TButton', 
                            font=('Segoe UI', 10), 
                            padding=6, 
                            relief='flat', 
                            background=self.colors['accent'], 
                            foreground=self.colors['fg_primary'])
        self.style.map('TButton', 
                      background=[('active', self.colors['accent_hover']), 
                                 ('disabled', self.colors['disabled'])],
                      foreground=[('disabled', self.colors['fg_muted'])])
        
        # Configure special button styles
        self.style.configure('Primary.TButton', background=self.colors['accent'], foreground='#ffffff')
        self.style.map('Primary.TButton', background=[('active', self.colors['accent_hover'])])
        
        self.style.configure('Success.TButton', background=self.colors['success'], foreground='#ffffff')
        self.style.map('Success.TButton', background=[('active', self.colors['success_hover'])])
        
        self.style.configure('Warning.TButton', background=self.colors['warning'], foreground='#212529')
        self.style.map('Warning.TButton', background=[('active', self.colors['warning_hover'])])
        
        self.style.configure('Danger.TButton', background=self.colors['danger'], foreground='#ffffff')
        self.style.map('Danger.TButton', background=[('active', self.colors['danger_hover'])])
        
        self.style.configure('Info.TButton', background=self.colors['info'], foreground='#212529')
        self.style.map('Info.TButton', background=[('active', self.colors['info_hover'])])
        
        # Configure label styles
        self.style.configure('TLabel', 
                            font=('Segoe UI', 10), 
                            background=self.colors['bg_primary'], 
                            foreground=self.colors['fg_primary'])
        self.style.configure('Title.TLabel', 
                            font=('Segoe UI', 14, 'bold'), 
                            background=self.colors['bg_primary'], 
                            foreground=self.colors['fg_primary'])
        self.style.configure('Subtitle.TLabel', 
                            font=('Segoe UI', 12, 'bold'), 
                            background=self.colors['bg_primary'], 
                            foreground=self.colors['fg_primary'])
        self.style.configure('Muted.TLabel', 
                            font=('Segoe UI', 10), 
                            background=self.colors['bg_primary'], 
                            foreground=self.colors['fg_muted'])
        
        # Configure entry styles
        self.style.configure('TEntry', 
                            padding=6, 
                            relief='flat', 
                            fieldbackground='#ffffff', 
                            borderwidth=1)
        self.style.map('TEntry', 
                      fieldbackground=[('disabled', self.colors['disabled'])],
                      bordercolor=[('focus', self.colors['accent'])])
        
        # Configure frame styles
        self.style.configure('Card.TFrame', 
                            relief='flat', 
                            borderwidth=1, 
                            background=self.colors['bg_secondary'])
        
        # Configure progress bar
        self.style.configure('TProgressbar', 
                            thickness=8, 
                            background=self.colors['accent'], 
                            troughcolor=self.colors['bg_tertiary'], 
                            borderwidth=0)
        
        # Configure Treeview (for lists and tables)
        self.style.configure('Treeview', 
                            background=self.colors['bg_secondary'],
                            fieldbackground=self.colors['bg_secondary'],
                            foreground=self.colors['fg_primary'])
        self.style.map('Treeview',
                      background=[('selected', self.colors['accent'])],
                      foreground=[('selected', '#ffffff')])
        
        # Configure Combobox
        self.style.configure('TCombobox', 
                            padding=5,
                            relief='flat',
                            fieldbackground='#ffffff')
        self.style.map('TCombobox',
                      fieldbackground=[('readonly', '#ffffff')],
                      selectbackground=[('readonly', self.colors['accent'])],
                      selectforeground=[('readonly', '#ffffff')])
        
        # Apply different styles based on screen size
        self._apply_responsive_styles()
    
    # Variable to control resize throttling
    _resize_timer_id = None
    
    def _on_resize(self, event):
        """Handle window resize events with throttling"""
        # Only process if it's the main window being resized
        if event.widget == self.root:
            # Cancel previous timer if exists
            if self._resize_timer_id:
                self.root.after_cancel(self._resize_timer_id)
            
            # Always update current dimensions immediately
            self.current_width = event.width
            self.current_height = event.height
            
            # Set a new timer to execute resize after a small delay
            self._resize_timer_id = self.root.after(100, self._do_resize)
    
    def _do_resize(self):
        """Execute the actual resize after throttling"""
        # Clear timer reference
        self._resize_timer_id = None
        
        # Apply responsive styles
        self._apply_responsive_styles()
        
        # Update status bar geometry with proper padding to prevent it from being cut off
        if hasattr(self.root, 'status_bar'):
            padding = 5  # Add padding to prevent cutting off
            self.root.status_bar.configure(width=self.current_width)
            self.root.status_bar.place(x=0, y=self.current_height-(20+padding), relwidth=1)
    
    def _apply_responsive_styles(self):
        """Apply styles based on current window size"""
        width = self.current_width
        
        # Small screens - more compact layout
        if width < self.breakpoints['small']:
            # Font adjustments
            self.style.configure('TNotebook.Tab', padding=[5, 3], font=('Segoe UI', 9))
            self.style.configure('TButton', font=('Segoe UI', 9), padding=4)
            self.style.configure('TLabel', font=('Segoe UI', 9))
            self.style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
            self.style.configure('Subtitle.TLabel', font=('Segoe UI', 10, 'bold'))
            self.style.configure('Muted.TLabel', font=('Segoe UI', 9))
            
            # Entry and frame adjustments
            self.style.configure('TEntry', padding=4)
            self.style.configure('TCombobox', padding=4)
        
        # Medium screens
        elif width < self.breakpoints['medium']:
            # Font adjustments
            self.style.configure('TNotebook.Tab', padding=[8, 4], font=('Segoe UI', 10))
            self.style.configure('TButton', font=('Segoe UI', 10), padding=5)
            self.style.configure('TLabel', font=('Segoe UI', 10))
            self.style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
            self.style.configure('Subtitle.TLabel', font=('Segoe UI', 12, 'bold'))
            self.style.configure('Muted.TLabel', font=('Segoe UI', 10))
            
            # Entry and frame adjustments
            self.style.configure('TEntry', padding=5)
            self.style.configure('TCombobox', padding=5)
        
        # Large screens
        else:
            # Font adjustments
            self.style.configure('TNotebook.Tab', padding=[12, 6], font=('Segoe UI', 11))
            self.style.configure('TButton', font=('Segoe UI', 11), padding=6)
            self.style.configure('TLabel', font=('Segoe UI', 11))
            self.style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'))
            self.style.configure('Subtitle.TLabel', font=('Segoe UI', 14, 'bold'))
            self.style.configure('Muted.TLabel', font=('Segoe UI', 11))
            
            # Entry and frame adjustments
            self.style.configure('TEntry', padding=6)
            self.style.configure('TCombobox', padding=6)
        
        # Configure progress bar consistently
        self.style.configure('TProgressbar', 
                            thickness=8, 
                            background=self.colors['accent'], 
                            troughcolor=self.colors['bg_tertiary'], 
                            borderwidth=0)
    
    def get_padding(self):
        """Return appropriate padding based on screen size"""
        width = self.current_width
        
        if width < self.breakpoints['small']:
            return 8
        elif width < self.breakpoints['medium']:
            return 12
        else:
            return 16
    
    def get_font_size(self, element_type='normal'):
        """Return appropriate font size based on screen size and element type"""
        width = self.current_width
        
        sizes = {
            'small': {
                'normal': 9,
                'title': 12,
                'subtitle': 10,
                'button': 9,
                'tab': 9,
                'input': 9
            },
            'medium': {
                'normal': 10,
                'title': 14,
                'subtitle': 12,
                'button': 10,
                'tab': 10,
                'input': 10
            },
            'large': {
                'normal': 11,
                'title': 16,
                'subtitle': 14,
                'button': 11,
                'tab': 11,
                'input': 11
            }
        }
        
        if width < self.breakpoints['small']:
            return sizes['small'][element_type]
        elif width < self.breakpoints['medium']:
            return sizes['medium'][element_type]
        else:
            return sizes['large'][element_type]

    def create_responsive_grid(self, parent, columns=2):
        """Create a responsive grid layout"""
        # Adjust columns based on window width
        if self.current_width < self.breakpoints['xsmall']:
            actual_columns = 1
            parent.config(padding=5)
        elif self.current_width < self.breakpoints['small']:
            actual_columns = min(columns, 2)
            parent.config(padding=8)
        elif self.current_width < self.breakpoints['medium']:
            actual_columns = min(columns, 3)
            parent.config(padding=12)
        elif self.current_width < self.breakpoints['large']:
            actual_columns = min(columns, 4)
            parent.config(padding=15)
        else:
            actual_columns = min(columns, 5)
            parent.config(padding=20)
        
        # Configure grid
        for i in range(actual_columns):
            parent.columnconfigure(i, weight=1)
        
        # Add appropriate padding based on screen size
        padding = self.get_padding()
        for widget in parent.winfo_children():
            widget.grid_configure(padx=padding, pady=padding)
            
            # Apply consistent styling to widgets based on their type
            if isinstance(widget, ttk.Label):
                widget.configure(style='TLabel')
            elif isinstance(widget, ttk.Button):
                widget.configure(style='TButton')
            elif isinstance(widget, ttk.Entry):
                widget.configure(style='TEntry')
            elif isinstance(widget, ttk.Frame):
                widget.configure(style='Card.TFrame')
        
        return actual_columns

def apply_theme(root):
    """Apply a modern theme to the application"""
    # Create a responsive UI instance to handle styling
    responsive_ui = ResponsiveUI(root)
    
    # Return the style object for further customization if needed
    return responsive_ui.style