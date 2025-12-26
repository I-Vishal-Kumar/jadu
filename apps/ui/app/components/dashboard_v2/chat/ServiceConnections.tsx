import React, { useState, useEffect } from 'react';
import {
    Mail,
    Video,
    CheckCircle,
    ExternalLink,
    Loader2,
    Github,
    Plus,
    Zap,
    AlertCircle,
    Trash2,
    Settings,
    ArrowRight
} from 'lucide-react';
import { useUser } from '@clerk/nextjs';
import ConnectionModal from './ConnectionModal';

interface Service {
    id: string;
    name: string;
    description: string;
    icon: React.ReactNode;
    color: string;
    isConnected: boolean;
}

const ServiceConnections: React.FC = () => {
    const { user } = useUser();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [loadingService, setLoadingService] = useState<string | null>(null);
    const [services, setServices] = useState<Service[]>([
        {
            id: 'zoho',
            name: 'Zoho Mail',
            description: 'Emails & Cliq Messages',
            icon: <Mail className="w-4 h-4" />,
            color: 'bg-red-500',
            isConnected: false,
        },
        {
            id: 'zoom',
            name: 'Zoom',
            description: 'Meetings & Scheduling',
            icon: <Video className="w-4 h-4" />,
            color: 'bg-blue-500',
            isConnected: false,
        },
        {
            id: 'github',
            name: 'GitHub',
            description: 'Issues & Pull Requests',
            icon: <Github className="w-4 h-4" />,
            color: 'bg-gray-800',
            isConnected: false,
        },
    ]);

    // Fetch connection status on mount
    useEffect(() => {
        fetchStatus();
    }, [user]);

    const fetchStatus = async () => {
        if (!user) return;
        try {
            const response = await fetch(`http://localhost:8004/api/oauth/status?user_id=${user.id}`);
            if (response.ok) {
                const data = await response.json();
                setServices(prev => prev.map(s => {
                    if (s.id === 'zoho') return { ...s, isConnected: data.zoho };
                    if (s.id === 'zoom') return { ...s, isConnected: data.zoom };
                    if (s.id === 'github') return { ...s, isConnected: data.github };
                    return s;
                }));
            }
        } catch (error) {
            console.error('Failed to fetch service status:', error);
        }
    };

    const handleConnect = (serviceId: string) => {
        if (!user) return;
        setLoadingService(serviceId);
        const userId = user.id;
        const width = 600, height = 700;
        const left = (window.screen.width - width) / 2;
        const top = (window.screen.height - height) / 2;

        const popup = window.open(
            `http://localhost:8004/api/oauth/${serviceId}/init?user_id=${userId}`,
            'OAuth Login',
            `width=${width},height=${height},left=${left},top=${top}`
        );

        // Poll for popup close
        const interval = setInterval(() => {
            if (popup?.closed) {
                clearInterval(interval);
                setLoadingService(null);
                setIsModalOpen(false);
                fetchStatus();
            }
        }, 500);
    };

    const connectedServices = services.filter(s => s.isConnected);
    const availableCount = services.length - connectedServices.length;

    return (
        <div className="flex-1 flex flex-col min-h-0 bg-white">
            {/* Header Area */}
            <div className="p-6 pb-4 shrink-0">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-xl font-bold text-gray-900">Connections</h2>
                        <p className="text-xs text-gray-500 mt-1">Manage your connected services</p>
                    </div>
                </div>

                <button
                    onClick={() => setIsModalOpen(true)}
                    className="w-full flex items-center justify-between p-4 bg-purple-50 hover:bg-purple-100 border border-purple-100 rounded-2xl transition-all group"
                >
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-purple-500/20 group-hover:scale-110 transition-transform">
                            <Plus size={20} />
                        </div>
                        <div className="text-left">
                            <span className="block text-sm font-bold text-purple-900 leading-tight">Explore Services</span>
                            <span className="text-[10px] text-purple-600 font-medium">{services.length} Premium integrations available</span>
                        </div>
                    </div>
                    <ArrowRight size={18} className="text-purple-400 group-hover:translate-x-1 transition-transform" />
                </button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto px-6 pb-6 min-h-0 space-y-6">
                {/* Connected List */}
                <div className="space-y-3">
                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">
                        Your Connections ({connectedServices.length})
                    </h3>

                    {connectedServices.length === 0 ? (
                        <div className="p-8 border-2 border-dashed border-gray-100 rounded-2xl flex flex-col items-center justify-center text-center space-y-3">
                            <div className="p-3 bg-gray-50 rounded-full text-gray-400">
                                <Zap size={24} />
                            </div>
                            <p className="text-xs text-gray-500 font-medium">No services connected yet. <br />Start by exploring integrations.</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {connectedServices.map((service) => (
                                <div
                                    key={service.id}
                                    className="flex items-center gap-3 p-3 bg-white border border-gray-100 rounded-xl hover:border-gray-200 transition-all hover:shadow-sm group"
                                >
                                    <div className={`w-8 h-8 ${service.color} rounded-lg flex items-center justify-center text-white shadow-sm shrink-0`}>
                                        {service.icon}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <h4 className="text-sm font-bold text-gray-900 truncate tracking-tight">{service.name}</h4>
                                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                                            title="Disconnect"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                        <button
                                            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all"
                                            title="Settings"
                                        >
                                            <Settings size={14} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Info Card */}
                <div className="p-4 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl text-white shadow-lg shadow-purple-500/20 relative overflow-hidden">
                    <Zap className="absolute -right-2 -bottom-2 w-20 h-20 text-white/10 rotate-12" />
                    <h4 className="text-sm font-bold mb-1 relative">AI-Powered Tools</h4>
                    <p className="text-[10px] text-purple-100 leading-relaxed relative font-medium opacity-90">
                        Once connected, your AI agent can automatically perform tasks like sending emails and checking your schedule.
                    </p>
                </div>
            </div>

            <ConnectionModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onConnect={handleConnect}
                loadingService={loadingService}
            />
        </div>
    );
};

export default ServiceConnections;
