// Shared timing for the sidebar and menu animations, matching the CSS in `starlight.css`.

export const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');

export const sidebarTiming: KeyframeAnimationOptions = {
	duration: 350,
	easing: 'cubic-bezier(0.32, 0.72, 0, 1)',
};

export const menuOpenTiming: KeyframeAnimationOptions = {
	duration: 180,
	easing: 'ease-out',
};

export const menuCloseTiming: KeyframeAnimationOptions = {
	duration: 140,
	easing: 'ease-in',
	fill: 'forwards',
};

/** Keyframes for a menu receding toward its anchor; reversed, they open it. */
export const menuCloseKeyframes: Keyframe[] = [
	{ opacity: 1, transform: 'none' },
	{ opacity: 0, transform: 'scale(0.98)' },
];
