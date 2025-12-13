import { ReactNode, ButtonHTMLAttributes } from 'react';
import { motion } from 'framer-motion';

interface ButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'onDrag' | 'onDragEnd' | 'onDragStart' | 'onAnimationStart' | 'onAnimationEnd'> {
    variant?: 'primary' | 'secondary';
    children: ReactNode;
    icon?: ReactNode;
    loading?: boolean;
}

export function Button({
    variant = 'primary',
    children,
    icon,
    loading,
    className = '',
    disabled,
    ...props
}: ButtonProps) {
    const baseClass = variant === 'primary' ? 'btn-primary' : 'btn-secondary';

    return (
        <motion.button
            className={`${baseClass} ${className}`}
            disabled={disabled || loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            {...(props as any)}
        >
            {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
                <>
                    {icon}
                    {children}
                </>
            )}
        </motion.button>
    );
}
