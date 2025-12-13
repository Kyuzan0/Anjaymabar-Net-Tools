import { motion } from 'framer-motion';

interface SkeletonProps {
    className?: string;
    variant?: 'text' | 'rectangle' | 'circle';
    width?: string | number;
    height?: string | number;
}

export function Skeleton({
    className = '',
    variant = 'rectangle',
    width,
    height
}: SkeletonProps) {
    const baseClasses = 'bg-white/10 animate-pulse';

    const variantClasses = {
        text: 'rounded',
        rectangle: 'rounded-lg',
        circle: 'rounded-full',
    };

    const style = {
        width: width || '100%',
        height: height || (variant === 'text' ? '1em' : '100%'),
    };

    return (
        <div
            className={`${baseClasses} ${variantClasses[variant]} ${className}`}
            style={style}
        />
    );
}

export function CardSkeleton() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-card space-y-4"
        >
            <Skeleton variant="text" width="40%" height={24} />
            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <div className="flex-1 space-y-2">
                        <Skeleton variant="text" width="60%" height={20} />
                        <Skeleton variant="text" width="80%" height={14} />
                    </div>
                    <Skeleton variant="rectangle" width={56} height={32} className="rounded-full" />
                </div>
                <div className="border-t border-white/10" />
                <div className="flex items-center justify-between">
                    <div className="flex-1 space-y-2">
                        <Skeleton variant="text" width="50%" height={20} />
                        <Skeleton variant="text" width="70%" height={14} />
                    </div>
                    <Skeleton variant="rectangle" width={56} height={32} className="rounded-full" />
                </div>
            </div>
        </motion.div>
    );
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
    return (
        <div className="space-y-2">
            {Array.from({ length: rows }).map((_, i) => (
                <div key={i} className="flex gap-4 p-3 bg-white/5 rounded-lg">
                    <Skeleton variant="rectangle" width={40} height={40} />
                    <div className="flex-1 space-y-2">
                        <Skeleton variant="text" width="60%" height={16} />
                        <Skeleton variant="text" width="40%" height={12} />
                    </div>
                    <Skeleton variant="rectangle" width={80} height={32} />
                </div>
            ))}
        </div>
    );
}

export function SettingsSkeleton() {
    return (
        <div className="p-6 space-y-6">
            {/* Header skeleton */}
            <div className="flex items-center gap-3">
                <Skeleton variant="circle" width={32} height={32} />
                <Skeleton variant="text" width={200} height={28} />
            </div>

            {/* Card skeleton */}
            <CardSkeleton />
            <CardSkeleton />

            {/* Buttons skeleton */}
            <div className="flex gap-3">
                <Skeleton variant="rectangle" width={150} height={44} />
                <Skeleton variant="rectangle" width={180} height={44} />
            </div>
        </div>
    );
}
