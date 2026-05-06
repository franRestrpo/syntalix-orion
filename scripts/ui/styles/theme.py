from .colors import Colors, COLORS
from .typography import Typography

class Theme:
    colors = Colors
    typography = Typography

    @classmethod
    def get_css_variables(cls) -> str:
        return f"""
:root {{
    --color-background: {cls.colors.background.hex6};
    --color-surface: {cls.colors.surface.hex6};
    --color-surface-elevated: {cls.colors.surface_elevated.hex6};

    --color-text-primary: {cls.colors.text_primary.hex6};
    --color-text-secondary: {cls.colors.text_secondary.hex6};
    --color-text-muted: {cls.colors.text_muted.hex6};

    --color-primary: {cls.colors.primary.hex6};
    --color-secondary: {cls.colors.secondary.hex6};

    --color-success: {cls.colors.success.hex6};
    --color-warning: {cls.colors.warning.hex6};
    --color-error: {cls.colors.error.hex6};

    --color-category-core: {cls.colors.category_core.hex6};
    --color-category-data: {cls.colors.category_data.hex6};
    --color-category-monitoring: {cls.colors.category_monitoring.hex6};
    --color-category-networking: {cls.colors.category_networking.hex6};
    --color-category-ai: {cls.colors.category_ai.hex6};
    --color-category-automation: {cls.colors.category_automation.hex6};
    --color-category-communication: {cls.colors.category_communication.hex6};
    --color-category-management: {cls.colors.category_management.hex6};
}}
"""

THEME = Theme()