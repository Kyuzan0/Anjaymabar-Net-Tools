/**
 * Validate IPv4 address format
 */
export function isValidIPv4(ip: string): boolean {
    if (!ip) return false;

    const pattern = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!pattern.test(ip)) return false;

    const parts = ip.split('.');
    return parts.every(part => {
        const num = parseInt(part, 10);
        return num >= 0 && num <= 255;
    });
}

/**
 * Validate subnet mask format
 */
export function isValidSubnetMask(mask: string): boolean {
    if (!isValidIPv4(mask)) return false;

    const validMasks = [
        '255.255.255.255', '255.255.255.254', '255.255.255.252',
        '255.255.255.248', '255.255.255.240', '255.255.255.224',
        '255.255.255.192', '255.255.255.128', '255.255.255.0',
        '255.255.254.0', '255.255.252.0', '255.255.248.0',
        '255.255.240.0', '255.255.224.0', '255.255.192.0',
        '255.255.128.0', '255.255.0.0', '255.254.0.0',
        '255.252.0.0', '255.248.0.0', '255.240.0.0',
        '255.224.0.0', '255.192.0.0', '255.128.0.0',
        '255.0.0.0', '254.0.0.0', '252.0.0.0',
        '248.0.0.0', '240.0.0.0', '224.0.0.0',
        '192.0.0.0', '128.0.0.0', '0.0.0.0'
    ];

    return validMasks.includes(mask);
}

/**
 * Convert CIDR prefix to subnet mask
 */
export function prefixToSubnet(prefix: number): string {
    if (prefix < 0 || prefix > 32) return '255.255.255.0';

    const mask = prefix === 0 ? 0 : (0xFFFFFFFF << (32 - prefix)) >>> 0;
    return [
        (mask >>> 24) & 0xFF,
        (mask >>> 16) & 0xFF,
        (mask >>> 8) & 0xFF,
        mask & 0xFF
    ].join('.');
}

/**
 * Convert subnet mask to CIDR prefix
 */
export function subnetToPrefix(subnet: string): number {
    if (!isValidIPv4(subnet)) return 24;

    const parts = subnet.split('.').map(p => parseInt(p, 10));
    let binary = '';
    for (const part of parts) {
        binary += part.toString(2).padStart(8, '0');
    }
    return (binary.match(/1/g) || []).length;
}

/**
 * Get IP address class
 */
export function getIPClass(ip: string): string {
    if (!isValidIPv4(ip)) return 'Invalid';

    const firstOctet = parseInt(ip.split('.')[0], 10);

    if (firstOctet >= 1 && firstOctet <= 126) return 'Class A';
    if (firstOctet === 127) return 'Loopback';
    if (firstOctet >= 128 && firstOctet <= 191) return 'Class B';
    if (firstOctet >= 192 && firstOctet <= 223) return 'Class C';
    if (firstOctet >= 224 && firstOctet <= 239) return 'Class D (Multicast)';
    if (firstOctet >= 240 && firstOctet <= 255) return 'Class E (Reserved)';

    return 'Unknown';
}

/**
 * Check if IP is private
 */
export function isPrivateIP(ip: string): boolean {
    if (!isValidIPv4(ip)) return false;

    const parts = ip.split('.').map(p => parseInt(p, 10));

    // 10.0.0.0 - 10.255.255.255
    if (parts[0] === 10) return true;

    // 172.16.0.0 - 172.31.255.255
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true;

    // 192.168.0.0 - 192.168.255.255
    if (parts[0] === 192 && parts[1] === 168) return true;

    return false;
}

/**
 * Format MAC address
 */
export function formatMacAddress(mac: string): string {
    if (!mac) return '';
    // Remove any existing separators and format with colons
    const clean = mac.replace(/[^a-fA-F0-9]/g, '');
    if (clean.length !== 12) return mac;
    return clean.match(/.{2}/g)?.join(':').toUpperCase() || mac;
}

/**
 * Validate form data for static IP configuration
 */
export interface IPFormValidation {
    isValid: boolean;
    errors: Record<string, string>;
}

export function validateIPForm(data: {
    ip_address: string;
    subnet_mask: string;
    gateway: string;
    primary_dns: string;
    secondary_dns: string;
}): IPFormValidation {
    const errors: Record<string, string> = {};

    if (!data.ip_address) {
        errors.ip_address = 'IP Address is required';
    } else if (!isValidIPv4(data.ip_address)) {
        errors.ip_address = 'Invalid IP address format';
    }

    if (!data.subnet_mask) {
        errors.subnet_mask = 'Subnet mask is required';
    } else if (!isValidSubnetMask(data.subnet_mask)) {
        errors.subnet_mask = 'Invalid subnet mask';
    }

    if (data.gateway && !isValidIPv4(data.gateway)) {
        errors.gateway = 'Invalid gateway format';
    }

    if (data.primary_dns && !isValidIPv4(data.primary_dns)) {
        errors.primary_dns = 'Invalid DNS format';
    }

    if (data.secondary_dns && !isValidIPv4(data.secondary_dns)) {
        errors.secondary_dns = 'Invalid DNS format';
    }

    return {
        isValid: Object.keys(errors).length === 0,
        errors
    };
}
