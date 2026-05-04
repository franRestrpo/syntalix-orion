from textual.color import Color

class Colors:
    background = Color.parse("#0D1117")
    surface = Color.parse("#161B22")
    surface_elevated = Color.parse("#21262D")

    text_primary = Color.parse("#F0F6FC")
    text_secondary = Color.parse("#8B949E")
    text_muted = Color.parse("#6E7681")

    primary = Color.parse("#00D9FF")
    secondary = Color.parse("#7C3AED")

    success = Color.parse("#10B981")
    warning = Color.parse("#F59E0B")
    error = Color.parse("#EF4444")

    category_core = Color.parse("#F472B6")
    category_data = Color.parse("#60A5FA")
    category_monitoring = Color.parse("#34D399")
    category_networking = Color.parse("#FBBF24")
    category_ai = Color.parse("#A78BFA")
    category_automation = Color.parse("#FB923C")
    category_communication = Color.parse("#38BDF8")
    category_management = Color.parse("#94A3B8")

    @classmethod
    def for_category(cls, category: str) -> Color:
        return getattr(cls, f"category_{category.lower()}", cls.primary)

COLORS = Colors()