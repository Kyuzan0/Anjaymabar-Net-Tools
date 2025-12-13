import { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface CardProps {
    children: ReactNode;
    className?: string;
    title?: string;
}

export function Card({ children, className = '', title }: CardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className={`glass-card ${className}`}
        >
            {title && (
                <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
            )}
            {children}
        </motion.div>
    );
}
