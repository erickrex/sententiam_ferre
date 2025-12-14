// Parameter options as defined in the design document
export const PARAMETER_OPTIONS = {
  art_style: [
    { value: 'cartoon', label: 'Cartoon', description: 'Bold outlines, exaggerated features' },
    { value: 'pixel_art', label: 'Pixel Art', description: 'Retro game aesthetic, limited palette' },
    { value: 'flat_vector', label: 'Flat Vector', description: 'Clean shapes, minimal shading' },
    { value: 'hand_drawn', label: 'Hand Drawn', description: 'Sketchy lines, organic feel' },
  ],
  view_angle: [
    { value: 'side_profile', label: 'Side Profile', description: 'Classic side-scrolling view' },
    { value: 'front_facing', label: 'Front Facing', description: 'Direct front view' },
    { value: 'three_quarter', label: 'Three Quarter', description: 'Angled perspective view' },
  ],
  pose: [
    { value: 'idle', label: 'Idle', description: 'Standing relaxed stance' },
    { value: 'action', label: 'Action', description: 'Dynamic movement pose' },
    { value: 'jumping', label: 'Jumping', description: 'Mid-air jump pose' },
    { value: 'attacking', label: 'Attacking', description: 'Aggressive attack stance' },
    { value: 'celebrating', label: 'Celebrating', description: 'Victory celebration pose' },
  ],
  expression: [
    { value: 'neutral', label: 'Neutral', description: 'Calm, default expression' },
    { value: 'happy', label: 'Happy', description: 'Joyful, smiling' },
    { value: 'angry', label: 'Angry', description: 'Fierce, determined' },
    { value: 'surprised', label: 'Surprised', description: 'Shocked, wide-eyed' },
    { value: 'determined', label: 'Determined', description: 'Focused, resolute' },
  ],
  background: [
    { value: 'transparent', label: 'Transparent', description: 'No background (PNG)' },
    { value: 'solid_color', label: 'Solid Color', description: 'Single color backdrop' },
    { value: 'simple_gradient', label: 'Simple Gradient', description: 'Subtle gradient backdrop' },
  ],
  color_palette: [
    { value: 'vibrant', label: 'Vibrant', description: 'Bright, saturated colors' },
    { value: 'pastel', label: 'Pastel', description: 'Soft, muted tones' },
    { value: 'muted', label: 'Muted', description: 'Desaturated, subtle colors' },
    { value: 'monochrome', label: 'Monochrome', description: 'Single color variations' },
  ],
};

export const PARAMETER_LABELS = {
  art_style: 'Art Style',
  view_angle: 'View Angle',
  pose: 'Pose',
  expression: 'Expression',
  background: 'Background',
  color_palette: 'Color Palette',
};

// Default parameter values
export const DEFAULT_PARAMETERS = {
  art_style: 'cartoon',
  view_angle: 'side_profile',
  pose: 'idle',
  expression: 'neutral',
  background: 'transparent',
  color_palette: 'vibrant',
};
