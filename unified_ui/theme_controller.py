"""Theme controller for the unified dashboard UI.

This module provides theme management functionality, including built-in light/dark
themes and custom themes. It handles theme switching and style application while
maintaining compatibility with Streamlit's native theme system.
"""
from typing import Any, Dict, Literal, Optional, Union

import streamlit as st

# Theme configuration constants
THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_CUSTOM = "custom"

ThemeType = Literal["light", "dark", "custom"]

# Theme configurations mapping
THEME_CONFIGS: Dict[str, Dict[str, Any]] = {
    THEME_LIGHT: {
        "base": "light",
    },
    THEME_DARK: {
        "base": "dark",
    },
    THEME_CUSTOM: {
        "base": "dark",
    },
}

def _init_theme_state() -> None:
    """Initialize theme-related session state if not already present."""
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = THEME_DARK
    if "theme_initialized" not in st.session_state:
        st.session_state.theme_initialized = False

def _apply_theme_styles(theme_config: Dict[str, Any]) -> None:
    """Apply theme-specific styles using custom CSS.
    
    Args:
        theme_config: Dictionary containing theme configuration parameters.
    """
    # Apply base theme
    st.markdown(f"""
        <style>
        /* Theme-specific styles */
        :root {{
            color-scheme: {theme_config['base']};
        }}
        </style>
    """, unsafe_allow_html=True)


# Theme name constants
THEME_DISPLAY_NAMES = {
    THEME_DARK: "深色",
    THEME_LIGHT: "淺色",
    THEME_CUSTOM: "自訂"
}

# Theme name to theme key mapping
THEME_NAME_MAP = {v: k for k, v in THEME_DISPLAY_NAMES.items()}


def switch_theme(theme: ThemeType) -> None:
    """Switch to the specified theme and apply its styles.
    
    Args:
        theme: The theme to switch to ("light", "dark", or "custom").
    """
    _init_theme_state()
    
    # Update theme only if changed
    if st.session_state.current_theme != theme:
        st.session_state.current_theme = theme
        config = THEME_CONFIGS[theme]
        _apply_theme_styles(config)
        st.session_state.theme_initialized = True


def render_theme_switcher() -> None:
    """在側邊欄應用全域樣式。"""
    with st.sidebar:
        st.markdown("""
            <style>
            /* Global Card Styles */
            .feature-card {
                background: var(--secondaryBackgroundColor);
                border: 1px solid var(--theme-customTheme-surface-border);
                border-radius: 1rem;
                padding: 1.5rem;
                margin: 0.5rem 0;
                transition: all 0.3s ease;
                box-shadow: var(--theme-customTheme-surface-shadow);
            }
            
            .feature-card:hover {
                transform: translateY(-3px);
                box-shadow: var(--theme-customTheme-card-hover-shadow);
            }
            
            /* Button Styles */
            .stButton > button {
                background: linear-gradient(135deg, 
                    var(--theme-customTheme-primary-gradient-start), 
                    var(--theme-customTheme-primary-gradient-end)
                ) !important;
                border: 1px solid transparent !important;
                border-radius: 0.5rem !important;
                color: white !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }
            
            .stButton > button:hover {
                box-shadow: var(--theme-customTheme-button-shadow) !important;
                transform: translateY(-1px) !important;
            }
            
            /* Hero Card Alignment */
            div.brand-hero {
                margin: 2rem auto !important;
                max-width: 1200px !important;
            }
            
            /* Feature Cards Container */
            div.feature-cards-container {
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 1rem;
                margin: 2rem auto;
                max-width: 1200px;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # 初始化主題狀態
        _init_theme_state()


def get_current_theme() -> str:
    """Get the name of the currently active theme.
    
    Returns:
        The current theme name ("light", "dark", or "custom").
    """
    _init_theme_state()
    return st.session_state.current_theme


def get_theme_config(theme: Optional[ThemeType] = None) -> Dict[str, Any]:
    """Get the configuration for the specified theme.
    
    Args:
        theme: Optional theme name. If None, returns current theme's config.
    
    Returns:
        Dictionary containing theme configuration parameters.
    """
    if theme is None:
        theme = get_current_theme()
    return THEME_CONFIGS[theme].copy()


def add_custom_theme(
    name: str,
    config: Dict[str, Any],
) -> None:
    """Add a new custom theme configuration.
    
    Args:
        name: Unique name for the custom theme.
        config: Theme configuration dictionary.
    
    Raises:
        ValueError: If name conflicts with built-in themes.
    """
    if name in {THEME_LIGHT, THEME_DARK}:
        raise ValueError(f"Cannot override built-in theme: {name}")
    THEME_CONFIGS[name] = config.copy()
