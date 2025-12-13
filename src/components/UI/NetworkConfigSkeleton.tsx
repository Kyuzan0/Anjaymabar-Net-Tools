/**
 * Skeleton loading components for Network Configuration form
 * Matches the exact layout of the IP Configuration card for seamless loading states
 */

import { motion } from 'framer-motion';
import { Skeleton } from './Skeleton';

/**
 * Props for FormFieldSkeleton component
 */
interface FormFieldSkeletonProps {
    /** Width of the label skeleton */
    labelWidth?: number | string;
    /** Additional class names */
    className?: string;
}

/**
 * Skeleton for a single form input field (label + input)
 * Matches the exact dimensions of form inputs in NetworkTab
 */
export function FormFieldSkeleton({ labelWidth = 80, className = '' }: FormFieldSkeletonProps) {
    return (
        <div className={`space-y-1 ${className}`}>
            <Skeleton 
                variant="text" 
                width={labelWidth} 
                height={14} 
            />
            <Skeleton 
                variant="rectangle" 
                height={44} 
                className="rounded-xl"
            />
        </div>
    );
}

/**
 * Main Network Configuration Skeleton
 * Matches the IP Configuration card layout exactly from NetworkTab.tsx
 */
export function NetworkConfigSkeleton() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="space-y-6"
        >
            {/* DHCP / Static Toggle Skeleton */}
            <div className="flex gap-4 mb-6">
                <div className="flex items-center gap-2">
                    <Skeleton variant="circle" width={16} height={16} />
                    <Skeleton variant="text" width={130} height={16} />
                </div>
                <div className="flex items-center gap-2">
                    <Skeleton variant="circle" width={16} height={16} />
                    <Skeleton variant="text" width={120} height={16} />
                </div>
            </div>

            {/* Form Fields Skeleton - matches grid layout from NetworkTab */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* IP Address */}
                <FormFieldSkeleton labelWidth={80} />
                
                {/* Subnet Mask */}
                <FormFieldSkeleton labelWidth={90} />
                
                {/* Default Gateway */}
                <FormFieldSkeleton labelWidth={110} />
                
                {/* Primary DNS */}
                <FormFieldSkeleton labelWidth={85} />
                
                {/* Secondary DNS */}
                <FormFieldSkeleton labelWidth={100} />
            </div>

            {/* Apply Button Skeleton */}
            <div className="mt-6">
                <Skeleton 
                    variant="rectangle" 
                    width={180} 
                    height={44} 
                    className="rounded-xl"
                />
            </div>
        </motion.div>
    );
}

/**
 * Skeleton for adapter dropdown section
 */
export function AdapterSelectSkeleton() {
    return (
        <div className="flex gap-2">
            <Skeleton 
                variant="rectangle" 
                height={48} 
                className="flex-1 rounded-xl"
            />
            <Skeleton 
                variant="rectangle" 
                width={48} 
                height={48} 
                className="rounded-xl"
            />
        </div>
    );
}

/**
 * Loading overlay for config card
 * Shows on top of existing content when switching adapters
 * Allows user to see previous data while new data loads
 */
export function ConfigLoadingOverlay() {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.1 }}
            className="absolute inset-0 bg-black/40 backdrop-blur-[1px] flex items-center justify-center z-10 rounded-xl"
        >
            <div className="flex flex-col items-center gap-3">
                {/* Animated spinner */}
                <div className="w-8 h-8 border-2 border-white/20 border-t-primary rounded-full animate-spin" />
                <span className="text-sm text-gray-300">Loading configuration...</span>
            </div>
        </motion.div>
    );
}

/**
 * Full page skeleton for initial Network page load
 * Shows while adapters are loading
 */
export function NetworkPageSkeleton() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 space-y-6"
        >
            {/* Header Skeleton */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Skeleton variant="circle" width={32} height={32} />
                    <Skeleton variant="text" width={180} height={28} />
                </div>
                <div className="flex gap-2">
                    <Skeleton variant="rectangle" width={100} height={40} className="rounded-xl" />
                    <Skeleton variant="rectangle" width={90} height={40} className="rounded-xl" />
                </div>
            </div>

            {/* Adapter Selection Skeleton */}
            <div className="glass-card p-4">
                <div className="flex flex-col gap-2">
                    <Skeleton variant="text" width={130} height={18} />
                    <AdapterSelectSkeleton />
                </div>
            </div>

            {/* IP Configuration Skeleton */}
            <div className="glass-card p-4">
                <Skeleton variant="text" width={140} height={20} className="mb-4" />
                <NetworkConfigSkeleton />
            </div>

            {/* Quick Commands Skeleton */}
            <div className="glass-card p-4">
                <Skeleton variant="text" width={110} height={20} className="mb-4" />
                <div className="flex flex-wrap gap-3">
                    {[100, 120, 95, 90, 100, 115].map((width, i) => (
                        <Skeleton 
                            key={i} 
                            variant="rectangle" 
                            width={width} 
                            height={40} 
                            className="rounded-xl"
                        />
                    ))}
                </div>
            </div>
        </motion.div>
    );
}

export default NetworkConfigSkeleton;