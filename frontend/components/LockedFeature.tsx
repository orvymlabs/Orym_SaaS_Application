/**
 * Locked Feature Component
 * Shows upgrade prompt for features locked behind paid plans
 */
"use client";
import { useRouter } from "next/navigation";
import { useTheme } from "@/lib/useTheme";

interface LockedFeatureProps {
  isLocked: boolean;
  children: React.ReactNode;
  featureName?: string;
  requiredPlan?: string;
  onUpgradeClick?: () => void;
  className?: string;
  showOverlay?: boolean;
}

export function LockedFeature({
  isLocked,
  children,
  featureName = "This feature",
  requiredPlan = "STARTER or PREMIUM",
  onUpgradeClick,
  className = "",
  showOverlay = true,
}: LockedFeatureProps) {
  const router = useRouter();
  const { isDark } = useTheme();

  const handleUpgrade = () => {
    if (onUpgradeClick) {
      onUpgradeClick();
    } else {
      router.push("/dashboard/subscription");
    }
  };

  if (!isLocked) {
    return <>{children}</>;
  }

  return (
    <div className={`relative ${className}`}>
      {/* Original content with reduced opacity */}
      <div className={showOverlay ? "opacity-50 pointer-events-none" : ""}>
        {children}
      </div>

      {/* Overlay with upgrade prompt */}
      {showOverlay && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div
            className={`rounded-[2rem] border-2 p-8 text-center max-w-md shadow-2xl backdrop-blur-sm ${
              isDark
                ? "bg-black/90 border-[#C9A84C]"
                : "bg-white/95 border-[#C9A84C]"
            }`}
          >
            <div className="text-4xl mb-4">🔒</div>
            <h3
              className={`text-xl font-black tracking-tight mb-2 ${
                isDark ? "text-white" : "text-slate-900"
              }`}
            >
              {featureName} Locked
            </h3>
            <p
              className={`text-sm font-medium mb-6 ${
                isDark ? "text-zinc-400" : "text-slate-600"
              }`}
            >
              Upgrade to <span className="font-black text-[#C9A84C]">{requiredPlan}</span> to unlock this feature
            </p>
            <button
              onClick={handleUpgrade}
              className="btn-primary w-full py-3 bg-gradient-to-r from-[#C9A84C] to-[#E8C97A] text-black hover:shadow-xl"
            >
              Upgrade Now
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

interface LockedButtonProps {
  isLocked: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
  disabled?: boolean;
  featureName?: string;
  requiredPlan?: string;
}

export function LockedButton({
  isLocked,
  onClick,
  children,
  className = "",
  disabled = false,
  featureName = "This feature",
  requiredPlan = "STARTER or PREMIUM",
}: LockedButtonProps) {
  const router = useRouter();
  const { isDark } = useTheme();

  const handleClick = () => {
    if (isLocked) {
      if (
        confirm(
          `${featureName} is locked on the FREE plan.\n\nUpgrade to ${requiredPlan} to unlock this feature.\n\nGo to subscription page?`
        )
      ) {
        router.push("/dashboard/subscription");
      }
    } else if (onClick && !disabled) {
      onClick();
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled && !isLocked}
      className={`${className} ${
        isLocked
          ? "relative overflow-hidden"
          : ""
      }`}
    >
      {isLocked && (
        <span className="absolute inset-0 flex items-center justify-center">
          🔒
        </span>
      )}
      <span className={isLocked ? "opacity-30" : ""}>{children}</span>
    </button>
  );
}
