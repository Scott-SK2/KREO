import tokens from "./tokens.json";

export { tokens };

export const colors = {
  taupe: tokens.color.taupe.value,
  taupeDark: tokens.color["taupe-dark"].value,
  brown: tokens.color.brown.value,
  ivory: tokens.color.ivory.value,
  paper: tokens.color.paper.value,
  ink: tokens.color.ink.value,
  gold: tokens.color.gold.value,
  bordeaux: tokens.color.bordeaux.value,
  white: tokens.color.white.value,
  success: tokens.color.success.value,
  warning: tokens.color.warning.value,
  danger: tokens.color.danger.value,
  focus: tokens.color.focus.value,
} as const;

export const fonts = {
  display: tokens.font.display.value,
  body: tokens.font.body.value,
} as const;

export const radius = tokens.radius;
export const shadow = tokens.shadow;
export const space = tokens.space;
export const motion = tokens.motion;
export const touchTarget = tokens.touchTarget.min;
export const brand = tokens.brand;

/** Preset Tailwind v4 : à injecter dans `@theme` via les variables CSS de tokens.css. */
export const tailwindTheme = {
  colors: {
    taupe: { DEFAULT: colors.taupe, dark: colors.taupeDark },
    brown: colors.brown,
    ivory: colors.ivory,
    paper: colors.paper,
    ink: colors.ink,
    gold: colors.gold,
    bordeaux: colors.bordeaux,
    success: colors.success,
    warning: colors.warning,
    danger: colors.danger,
  },
  fontFamily: {
    display: fonts.display,
    body: fonts.body,
  },
} as const;

export type KreoColor = keyof typeof colors;
