import React from "react";

type LogoVariant = "full" | "text" | "symbol";

const SRC = {
  full: {
    dark: "/logos/orvym-nexus-logo-light.png",
    light: "/logos/orvym-nexus-logo-dark.png",
  },
  text: {
    dark: "/logos/orvym-nexus-text-light.png",
    light: "/logos/orvym-nexus-text-dark.png",
  },
  symbol: {
    dark: "/logos/orvym-symbol.png",
    light: "/logos/orvym-symbol.png",
  },
} as const;

export function Logo({
  variant = "full",
  theme = "dark",
  className = "",
  alt = "ORVYM NEXUS",
  fallbackText = "ORVYM",
}: {
  variant?: LogoVariant;
  theme?: "dark" | "light";
  className?: string;
  alt?: string;
  fallbackText?: string;
}) {
  const [errored, setErrored] = React.useState(false);
  const isDark = theme === "dark";
  const src = SRC[variant][isDark ? "dark" : "light"];

  if (errored) {
    return (
      <span className={`font-black tracking-tight ${className}`}>{fallbackText}</span>
    );
  }

  // eslint-disable-next-line @next/next/no-img-element
  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setErrored(true)}
    />
  );
}

