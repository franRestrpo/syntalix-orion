class Typography:
    font_family = "JetBrains Mono, Fira Code, Caskaydia Cove Nerd Font, monospace"

    title_size = 1.3
    subtitle_size = 1.1
    body_size = 1.0
    muted_size = 0.85

    title_weight = "bold"
    subtitle_weight = "medium"
    body_weight = "normal"
    muted_weight = "normal"

    @staticmethod
    def get_title_style() -> dict:
        return {"color": "#FFFFFF", "weight": "bold", "size": 1.3}

    @staticmethod
    def get_subtitle_style() -> dict:
        return {"color": "#8B949E", "weight": "medium", "size": 1.1}

    @staticmethod
    def get_body_style() -> dict:
        return {"color": "#E2E8F0", "weight": "normal", "size": 1.0}

    @staticmethod
    def get_muted_style() -> dict:
        return {"color": "#6E7681", "weight": "normal", "size": 0.85}