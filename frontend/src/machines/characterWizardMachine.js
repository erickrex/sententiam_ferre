/**
 * FIBO Parameter mappings for 2D game characters
 * These map user-friendly choices to actual backend API parameters
 * 
 * Backend expects:
 * - description (required)
 * - art_style: 'cartoon' | 'pixel_art' | 'flat_vector' | 'hand_drawn'
 * - view_angle: 'side_profile' | 'front_facing' | 'three_quarter'
 * - pose: 'idle' | 'action' | 'jumping' | 'attacking' | 'celebrating'
 * - expression: 'neutral' | 'happy' | 'angry' | 'surprised' | 'determined'
 * - background: 'transparent' | 'solid_color' | 'simple_gradient'
 * - color_palette: 'vibrant' | 'pastel' | 'muted' | 'monochrome'
 */

/**
 * Step configurations with visual options
 * Each option's `id` maps directly to the backend API value
 */
export const WIZARD_STEPS = {
  artStyle: {
    title: 'Pick your art style',
    subtitle: 'This defines the visual aesthetic',
    apiField: 'art_style',
    options: [
      { id: 'cartoon', label: 'Cartoon', icon: '🎨', description: 'Bold outlines, expressive' },
      { id: 'pixel_art', label: 'Pixel Art', icon: '👾', description: 'Retro 8-bit style' },
      { id: 'flat_vector', label: 'Flat Vector', icon: '📐', description: 'Clean, minimal shapes' },
      { id: 'hand_drawn', label: 'Hand Drawn', icon: '✏️', description: 'Sketchy, artistic style' },
    ],
  },
  viewAngle: {
    title: 'Camera angle',
    subtitle: 'How should we frame the character?',
    apiField: 'view_angle',
    options: [
      { id: 'front_facing', label: 'Front View', icon: '⬆️', description: 'Direct facing' },
      { id: 'side_profile', label: 'Side Profile', icon: '➡️', description: 'Classic platformer' },
      { id: 'three_quarter', label: '3/4 View', icon: '↗️', description: 'Angled perspective' },
    ],
  },
  pose: {
    title: 'Character pose',
    subtitle: 'What action are they doing?',
    apiField: 'pose',
    options: [
      { id: 'idle', label: 'Idle', icon: '🧍', description: 'Standing relaxed' },
      { id: 'action', label: 'Action', icon: '🏃', description: 'Running/moving' },
      { id: 'jumping', label: 'Jumping', icon: '⬆️', description: 'Mid-air leap' },
      { id: 'attacking', label: 'Attack', icon: '⚔️', description: 'Combat stance' },
      { id: 'celebrating', label: 'Celebrate', icon: '🎉', description: 'Victory pose' },
    ],
  },
  expression: {
    title: 'Facial expression',
    subtitle: 'Set the character mood',
    apiField: 'expression',
    options: [
      { id: 'neutral', label: 'Neutral', icon: '😐', description: 'Calm, default' },
      { id: 'happy', label: 'Happy', icon: '😊', description: 'Smiling, cheerful' },
      { id: 'angry', label: 'Angry', icon: '😠', description: 'Fierce, intense' },
      { id: 'surprised', label: 'Surprised', icon: '😮', description: 'Shocked, amazed' },
      { id: 'determined', label: 'Determined', icon: '😤', description: 'Focused, resolute' },
    ],
  },
  colorPalette: {
    title: 'Color palette',
    subtitle: 'Choose the color mood',
    apiField: 'color_palette',
    options: [
      { id: 'vibrant', label: 'Vibrant', icon: '🔴', description: 'Bright, saturated' },
      { id: 'pastel', label: 'Pastel', icon: '🩷', description: 'Soft, muted tones' },
      { id: 'muted', label: 'Muted', icon: '🖤', description: 'Subdued, earthy' },
      { id: 'monochrome', label: 'Monochrome', icon: '⬛', description: 'Single color family' },
    ],
  },
  background: {
    title: 'Background style',
    subtitle: 'What goes behind the character?',
    apiField: 'background',
    options: [
      { id: 'transparent', label: 'Transparent', icon: '🔲', description: 'No background (PNG)' },
      { id: 'solid_color', label: 'Solid Color', icon: '🟦', description: 'Single flat color' },
      { id: 'simple_gradient', label: 'Gradient', icon: '🌈', description: 'Smooth color blend' },
    ],
  },
};

/**
 * Step order for the wizard flow
 */
export const STEP_ORDER = [
  'description',
  'artStyle', 
  'viewAngle',
  'pose',
  'expression',
  'colorPalette',
  'background',
  'review',
  'generating',
  'complete'
];

/**
 * Build the API request parameters from wizard choices
 */
export const buildApiParams = (context) => {
  const { choices, description } = context;
  
  return {
    description: description || 'A 2D game character',
    art_style: choices.artStyle || 'cartoon',
    view_angle: choices.viewAngle || 'front_facing',
    pose: choices.pose || 'idle',
    expression: choices.expression || 'neutral',
    color_palette: choices.colorPalette || 'vibrant',
    background: choices.background || 'transparent',
  };
};

/**
 * Build the FIBO JSON preview from wizard choices
 * This is for display purposes to show the structured control
 */
export const buildFiboJson = (context) => {
  const { choices, description } = context;
  
  const fiboJson = {
    prompt: description || 'A 2D game character',
    parameters: {
      style: {
        art_style: choices.artStyle || 'cartoon',
        color_palette: choices.colorPalette || 'vibrant',
      },
      camera: {
        view_angle: choices.viewAngle || 'front_facing',
      },
      character: {
        pose: choices.pose || 'idle',
        expression: choices.expression || 'neutral',
      },
      output: {
        background: choices.background || 'transparent',
        format: 'png',
        resolution: '1024x1024',
      },
    },
  };
  
  return fiboJson;
};
