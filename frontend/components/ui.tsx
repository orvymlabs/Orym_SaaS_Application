import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  description?: string;
}

export const Card: React.FC<CardProps> = ({ children, className = "", title, description }) => {
  return (
    <div className={`bg-white dark:bg-[#090909] rounded-[2.5rem] border border-slate-200 dark:border-zinc-800 shadow-xl p-8 ${className}`}>
      {(title || description) && (
        <div className="mb-6">
          {title && <h3 className="text-xl font-black tracking-tight text-slate-900 dark:text-white uppercase tracking-widest text-xs">{title}</h3>}
          {description && <p className="text-sm text-slate-500 dark:text-zinc-500 mt-1 font-medium">{description}</p>}
        </div>
      )}
      {children}
    </div>
  );
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "success" | "icon";
  loading?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  loading = false,
  children,
  disabled,
  className = "",
  ...props
}) => {
  const variantClasses = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    danger: "btn-danger",
    success: "btn-success",
    icon: "btn-icon",
  };

  const combinedClasses = `${variantClasses[variant]} ${className}`;

  return (
    <button
      className={combinedClasses}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="flex items-center justify-center gap-2">
          <LoadingSpinner size="sm" color={variant === 'secondary' || variant === 'icon' ? 'current' : 'white'} />
          {variant !== 'icon' && "Processing..."}
        </span>
      ) : (
        children
      )}
    </button>
  );
};

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  className = "",
  id,
  icon,
  ...props
}) => {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="space-y-2">
      {label && (
        <label htmlFor={inputId} className="block text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-zinc-600 ml-1">
          {label}
        </label>
      )}
      <div className={icon ? "search-input-wrapper" : "relative"}>
        {icon && <div className="search-input-icon">{icon}</div>}
        <input
          id={inputId}
          className={`${icon ? 'search-input-field' : 'input-field'} ${error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/10' : ''} ${className}`}
          {...props}
        />
      </div>
      {error && <p className="text-[10px] font-bold text-rose-500 ml-1">{error}</p>}
      {helperText && !error && <p className="text-[10px] font-medium text-slate-400 dark:text-zinc-600 ml-1">{helperText}</p>}
    </div>
  );
};

export const TextArea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string; error?: string }> = ({
  label,
  error,
  className = "",
  id,
  ...props
}) => {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="space-y-2">
      {label && (
        <label htmlFor={inputId} className="block text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-zinc-600 ml-1">
          {label}
        </label>
      )}
      <textarea
        id={inputId}
        className={`textarea-field ${error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/10' : ''} ${className}`}
        {...props}
      />
      {error && <p className="text-[10px] font-bold text-rose-500 ml-1">{error}</p>}
    </div>
  );
};

export const Select: React.FC<React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string; error?: string; options: Array<{ value: string; label: string }> }> = ({
  label,
  error,
  options,
  className = "",
  id,
  ...props
}) => {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="space-y-2">
      {label && (
        <label htmlFor={inputId} className="block text-[10px] font-black uppercase tracking-widest text-slate-400 dark:text-zinc-600 ml-1">
          {label}
        </label>
      )}
      <select
        id={inputId}
        className={`select-field ${error ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500/10' : ''} ${className}`}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-[10px] font-bold text-rose-500 ml-1">{error}</p>}
    </div>
  );
};

export const LoadingSpinner: React.FC<{ size?: "sm" | "md" | "lg"; color?: string; className?: string }> = ({
  size = "md",
  color = "blue",
  className = "",
}) => {
  const sizeClasses = {
    sm: "w-4 h-4 border-2",
    md: "w-8 h-8 border-3",
    lg: "w-12 h-12 border-4",
  };

  const colorClasses = color === 'white' ? 'border-white/30 border-t-white' : 'border-slate-200 border-t-[#6c4ef2]';

  return (
    <div className={`inline-block animate-spin rounded-full ${sizeClasses[size]} ${colorClasses} ${className}`} role="status">
      <span className="sr-only">Loading...</span>
    </div>
  );
};

export const Badge: React.FC<{ children: React.ReactNode; variant?: "default" | "success" | "warning" | "error" | "info"; className?: string }> = ({
  variant = "default",
  children,
  className = "",
}) => {
  const variantClasses = {
    default: "bg-slate-100 text-slate-500 dark:bg-zinc-800 dark:text-zinc-400",
    success: "badge-success",
    warning: "bg-amber-50 text-amber-600 dark:bg-amber-900/20 dark:text-amber-500",
    error: "bg-rose-50 text-rose-600 dark:bg-rose-900/20 dark:text-rose-500",
    info: "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-500",
  };

  return (
    <span className={`badge ${variantClasses[variant]} ${className}`}>
      {children}
    </span>
  );
};

export const Toast: React.FC<{ message: string; type?: "success" | "error" | "info" | "warning"; onClose: () => void }> = ({ message, type = "info", onClose }) => {
  const bgColors = {
    success: "bg-emerald-50 border-emerald-100 dark:bg-emerald-900/20 dark:border-emerald-800",
    error: "bg-rose-50 border-rose-100 dark:bg-rose-900/20 dark:border-rose-800",
    info: "bg-blue-50 border-blue-100 dark:bg-blue-900/20 dark:border-blue-800",
    warning: "bg-amber-50 border-amber-100 dark:bg-amber-900/20 dark:border-amber-800",
  };

  const textColors = {
    success: "text-emerald-700 dark:text-emerald-400",
    error: "text-rose-700 dark:text-rose-400",
    info: "text-blue-700 dark:text-blue-400",
    warning: "text-amber-700 dark:text-amber-400",
  };

  const icons = {
    success: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
    ),
    error: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
    ),
    info: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
    ),
    warning: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
    ),
  };

  React.useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`${bgColors[type]} border rounded-2xl shadow-2xl p-5 flex items-start gap-4 min-w-[340px] max-w-[480px] animate-slide-in-right`}>
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${textColors[type]} bg-white/20 dark:bg-black/20`}>{icons[type]}</div>
      <p className={`text-xs font-bold uppercase tracking-tight flex-1 py-1.5 ${textColors[type]}`}>{message}</p>
      <button onClick={onClose} className={`flex-shrink-0 p-1.5 rounded-lg hover:bg-white/30 dark:hover:bg-black/30 transition-colors ${textColors[type]}`}>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>
    </div>
  );
};

export const useToast = () => {
  const [toasts, setToasts] = React.useState<Array<{ id: number; message: string; type: "success" | "error" | "info" | "warning" }>>([]);

  const showToast = React.useCallback((message: string, type: "success" | "error" | "info" | "warning" = "info") => {
    const id = Date.now() + Math.random();
    setToasts(prev => [...prev, { id, message, type }]);
  }, []);

  const removeToast = React.useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const ToastContainer = React.useCallback(() => (
    <div className="fixed top-6 right-6 z-[9999] flex flex-col gap-4 pointer-events-none">
      {toasts.map(t => (
        <div key={t.id} className="pointer-events-auto">
          <Toast message={t.message} type={t.type} onClose={() => removeToast(t.id)} />
        </div>
      ))}
    </div>
  ), [toasts, removeToast]);

  return { showToast, ToastContainer, toasts };
};
