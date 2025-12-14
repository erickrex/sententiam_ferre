"""
Prompt builder for BRIA FIBO API.

This module provides the PromptBuilder class for constructing
FIBO-compatible prompts from user input and style parameters.
"""
from typing import Dict, Optional


# Valid parameter options for character generation
VALID_ART_STYLES = frozenset(["cartoon", "pixel_art", "flat_vector", "hand_drawn"])
VALID_VIEW_ANGLES = frozenset(["side_profile", "front_facing", "three_quarter"])
VALID_POSES = frozenset(["idle", "action", "jumping", "attacking", "celebrating"])
VALID_EXPRESSIONS = frozenset(["neutral", "happy", "angry", "surprised", "determined"])
VALID_BACKGROUNDS = frozenset(["transparent", "solid_color", "simple_gradient"])
VALID_COLOR_PALETTES = frozenset(["vibrant", "pastel", "muted", "monochrome"])


class PromptBuilderError(Exception):
    """Exception raised for prompt building errors."""
    pass


class PromptBuilder:
    """
    Builds FIBO-compatible prompts from character descriptions and parameters.
    
    This class combines user-provided character descriptions with style modifiers
    to create prompts optimized for BRIA's text-to-image generation.
    """
    
    # Style modifiers for art styles
    STYLE_MODIFIERS: Dict[str, str] = {
        "cartoon": "cartoon style, bold outlines, exaggerated features, clean lines",
        "pixel_art": "pixel art style, retro game aesthetic, limited color palette, crisp pixels",
        "flat_vector": "flat vector style, clean geometric shapes, minimal shading, modern design",
        "hand_drawn": "hand-drawn style, sketchy lines, organic feel, artistic strokes",
    }
    
    # Pose modifiers
    POSE_MODIFIERS: Dict[str, str] = {
        "idle": "standing idle pose, relaxed stance",
        "action": "dynamic action pose, movement energy",
        "jumping": "mid-jump pose, airborne, dynamic",
        "attacking": "attack pose, aggressive stance, powerful",
        "celebrating": "celebration pose, arms raised, joyful",
    }
    
    # Expression modifiers
    EXPRESSION_MODIFIERS: Dict[str, str] = {
        "neutral": "neutral expression, calm face",
        "happy": "happy expression, smiling, cheerful",
        "angry": "angry expression, fierce look, intense",
        "surprised": "surprised expression, wide eyes, shocked",
        "determined": "determined expression, focused, resolute",
    }
    
    # View angle modifiers
    VIEW_ANGLE_MODIFIERS: Dict[str, str] = {
        "side_profile": "side view, profile perspective",
        "front_facing": "front view, facing forward",
        "three_quarter": "three-quarter view, slight angle",
    }
    
    # Background modifiers
    BACKGROUND_MODIFIERS: Dict[str, str] = {
        "transparent": "transparent background, isolated character",
        "solid_color": "solid color background, clean backdrop",
        "simple_gradient": "simple gradient background, subtle depth",
    }
    
    # Color palette modifiers
    COLOR_PALETTE_MODIFIERS: Dict[str, str] = {
        "vibrant": "vibrant colors, bold and saturated",
        "pastel": "pastel colors, soft and gentle tones",
        "muted": "muted colors, subdued palette",
        "monochrome": "monochrome palette, single color variations",
    }
    
    def build_prompt(
        self,
        description: str,
        art_style: str,
        view_angle: str,
        pose: str = "idle",
        expression: str = "neutral",
        background: str = "transparent",
        color_palette: str = "vibrant",
    ) -> str:
        """
        Build a FIBO-compatible prompt from description and parameters.
        
        Args:
            description: Character description (e.g., "friendly robot sidekick").
            art_style: Art style from VALID_ART_STYLES.
            view_angle: View angle from VALID_VIEW_ANGLES.
            pose: Character pose from VALID_POSES (default: "idle").
            expression: Facial expression from VALID_EXPRESSIONS (default: "neutral").
            background: Background type from VALID_BACKGROUNDS (default: "transparent").
            color_palette: Color palette from VALID_COLOR_PALETTES (default: "vibrant").
        
        Returns:
            A formatted prompt string for the BRIA FIBO API.
        
        Raises:
            PromptBuilderError: If any parameter is invalid.
        """
        # Validate parameters
        self._validate_parameters(
            art_style=art_style,
            view_angle=view_angle,
            pose=pose,
            expression=expression,
            background=background,
            color_palette=color_palette,
        )
        
        # Build the prompt components
        components = [
            f"A {description.strip()}",
            self.STYLE_MODIFIERS[art_style],
            "2D mobile game character",
            self.VIEW_ANGLE_MODIFIERS[view_angle],
            self.POSE_MODIFIERS[pose],
            self.EXPRESSION_MODIFIERS[expression],
            self.COLOR_PALETTE_MODIFIERS[color_palette],
            self.BACKGROUND_MODIFIERS[background],
        ]
        
        return ", ".join(components)
    
    def apply_style_modifiers(self, base: str, art_style: str) -> str:
        """
        Apply art style modifiers to a base prompt.
        
        Args:
            base: The base prompt string.
            art_style: Art style from VALID_ART_STYLES.
        
        Returns:
            The prompt with style modifiers applied.
        
        Raises:
            PromptBuilderError: If art_style is invalid.
        """
        if art_style not in VALID_ART_STYLES:
            raise PromptBuilderError(
                f"Invalid art_style: {art_style}. "
                f"Must be one of: {', '.join(sorted(VALID_ART_STYLES))}"
            )
        
        return f"{base}, {self.STYLE_MODIFIERS[art_style]}"
    
    def _validate_parameters(
        self,
        art_style: str,
        view_angle: str,
        pose: str,
        expression: str,
        background: str,
        color_palette: str,
    ) -> None:
        """
        Validate all generation parameters.
        
        Raises:
            PromptBuilderError: If any parameter is invalid.
        """
        errors = []
        
        if art_style not in VALID_ART_STYLES:
            errors.append(
                f"Invalid art_style: {art_style}. "
                f"Must be one of: {', '.join(sorted(VALID_ART_STYLES))}"
            )
        
        if view_angle not in VALID_VIEW_ANGLES:
            errors.append(
                f"Invalid view_angle: {view_angle}. "
                f"Must be one of: {', '.join(sorted(VALID_VIEW_ANGLES))}"
            )
        
        if pose not in VALID_POSES:
            errors.append(
                f"Invalid pose: {pose}. "
                f"Must be one of: {', '.join(sorted(VALID_POSES))}"
            )
        
        if expression not in VALID_EXPRESSIONS:
            errors.append(
                f"Invalid expression: {expression}. "
                f"Must be one of: {', '.join(sorted(VALID_EXPRESSIONS))}"
            )
        
        if background not in VALID_BACKGROUNDS:
            errors.append(
                f"Invalid background: {background}. "
                f"Must be one of: {', '.join(sorted(VALID_BACKGROUNDS))}"
            )
        
        if color_palette not in VALID_COLOR_PALETTES:
            errors.append(
                f"Invalid color_palette: {color_palette}. "
                f"Must be one of: {', '.join(sorted(VALID_COLOR_PALETTES))}"
            )
        
        if errors:
            raise PromptBuilderError("; ".join(errors))
    
    @staticmethod
    def get_valid_options() -> Dict[str, list]:
        """
        Get all valid parameter options.
        
        Returns:
            Dictionary mapping parameter names to their valid options.
        """
        return {
            "art_style": sorted(VALID_ART_STYLES),
            "view_angle": sorted(VALID_VIEW_ANGLES),
            "pose": sorted(VALID_POSES),
            "expression": sorted(VALID_EXPRESSIONS),
            "background": sorted(VALID_BACKGROUNDS),
            "color_palette": sorted(VALID_COLOR_PALETTES),
        }
