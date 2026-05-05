 "use client";
 
 import * as React from "react";
 
 export type Theme = "dark" | "light";
 
 function getInitialTheme(): Theme {
   if (typeof window === "undefined") return "dark";
   const t = window.localStorage.getItem("theme");
   return t === "light" ? "light" : "dark";
 }
 
 export function useTheme() {
   const [theme, setTheme] = React.useState<Theme>(getInitialTheme);
 
   React.useEffect(() => {
     const onStorage = (e: StorageEvent) => {
       if (e.key !== "theme") return;
       const next = e.newValue === "light" ? "light" : "dark";
       setTheme(next);
     };
 
     const onThemeChanged = (e: Event) => {
       const ce = e as CustomEvent<{ theme?: Theme }>;
       const next = ce.detail?.theme;
       if (next === "dark" || next === "light") setTheme(next);
       else setTheme(getInitialTheme());
     };
 
     window.addEventListener("storage", onStorage);
     window.addEventListener("theme-changed", onThemeChanged as EventListener);
     return () => {
       window.removeEventListener("storage", onStorage);
       window.removeEventListener("theme-changed", onThemeChanged as EventListener);
     };
   }, []);
 
   return { theme, isDark: theme === "dark" };
 }
 
