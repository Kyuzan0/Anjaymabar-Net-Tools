import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, Info, Loader2 } from 'lucide-react';

type StatusType = 'success' | 'error' | 'warning' | 'info' | 'loading';

interface StatusBadgeProps {
    status: StatusType;
    text?: string;
    size?: 'sm' | 'md' | 'lg';
    animate?: boolean;
}

const statusConfig = {
    success: {
        icon: CheckCircle,
        bgColor: 'bg-green-500/20',
        textColor: 'text-green-400',
        borderColor: 'border-green-500/30',
    },
    error: {
        icon: XCircle,
        bgColor: 'bg-red-500/20',
        textColor: 'text-red-400',
        borderColor: 'border-red-500/30',
    },
    warning: {
        icon: AlertTriangle,
        bgColor: 'bg-amber-500/20',
        textColor: 'text-amber-400',
        borderColor: 'border-amber-500/30',
    },
    info: {
        icon: Info,
        bgColor: 'bg-blue-500/20',
        textColor: 'text-blue-400',
        borderColor: 'border-blue-500/30',
    },
    loading: {
        icon: Loader2,
        bgColor: 'bg-gray-500/20',
        textColor: 'text-gray-400',
        borderColor: 'border-gray-500/30',
    },
};

const sizeConfig = {
    sm: { padding: 'px-2 py-0.5', text: 'text-xs', icon: 'w-3 h-3' },
    md: { padding: 'px-3 py-1', text: 'text-sm', icon: 'w-4 h-4' },
    lg: { padding: 'px-4 py-1.5', text: 'text-base', icon: 'w-5 h-5' },
};

export function StatusBadge({
    status,
    text,
    size = 'md',
    animate = true
}: StatusBadgeProps) {
    const config = statusConfig[status];
    const sizeStyles = sizeConfig[size];
    const Icon = config.icon;

    const content = (
        <span className={`
      inline-flex items-center gap-1.5 rounded-full border
      ${config.bgColor} ${config.textColor} ${config.borderColor}
      ${sizeStyles.padding} ${sizeStyles.text}
      font-medium
    `}>
            <Icon className={`${sizeStyles.icon} ${status === 'loading' ? 'animate-spin' : ''}`} />
            {text && <span>{text}</span>}
        </span>
    );

    if (animate && status !== 'loading') {
        return (
            <motion.span
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
            >
                {content}
            </motion.span>
        );
    }

    return content;
}

interface ConnectionStatusProps {
    isOnline: boolean;
    showText?: boolean;
}

export function ConnectionStatus({ isOnline, showText = true }: ConnectionStatusProps) {
    return (
        <StatusBadge
            status={isOnline ? 'success' : 'error'}
            text={showText ? (isOnline ? 'Online' : 'Offline') : undefined}
            size="sm"
        />
    );
}

interface AdminStatusProps {
    isAdmin: boolean | null;
    checking?: boolean;
}

export function AdminStatus({ isAdmin, checking }: AdminStatusProps) {
    if (checking) {
        return <StatusBadge status="loading" text="Checking..." size="sm" />;
    }

    return (
        <StatusBadge
            status={isAdmin ? 'success' : 'warning'}
            text={isAdmin ? 'Administrator' : 'Limited'}
            size="sm"
        />
    );
}

interface FeatureStatusProps {
    enabled: boolean;
    enabledText?: string;
    disabledText?: string;
}

export function FeatureStatus({
    enabled,
    enabledText = 'Enabled',
    disabledText = 'Disabled'
}: FeatureStatusProps) {
    return (
        <StatusBadge
            status={enabled ? 'success' : 'error'}
            text={enabled ? enabledText : disabledText}
            size="sm"
        />
    );
}
