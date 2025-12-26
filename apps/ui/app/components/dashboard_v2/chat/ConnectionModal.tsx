import React, { useState } from 'react';
import {
    X,
    Search,
    Mail,
    Video,
    Github,
    MessageSquare,
    Globe,
    Cloud,
    FileText,
    Shield,
    Plus,
    CheckCircle2,
    ArrowRight,
    Loader2
} from 'lucide-react';

interface ServiceOption {
    id: string;
    name: string;
    description: string;
    icon: React.ReactNode;
    color: string;
    textColor: string;
    isImplemented: boolean;
}

interface ConnectionModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConnect: (serviceId: string) => void;
    loadingService?: string | null;
}

const services: ServiceOption[] = [
    {
        id: 'zoho',
        name: 'Zoho Mail',
        description: 'Sync your emails and calendars',
        icon: <Mail className="w-6 h-6" />,
        color: 'bg-red-500',
        textColor: 'text-red-600',
        isImplemented: true,
    },
    {
        id: 'zoom',
        name: 'Zoom',
        description: 'Schedule and manage meetings',
        icon: <Video className="w-6 h-6" />,
        color: 'bg-blue-500',
        textColor: 'text-blue-600',
        isImplemented: true,
    },
    {
        id: 'github',
        name: 'GitHub',
        description: 'Manage issues and pull requests',
        icon: <Github className="w-6 h-6" />,
        color: 'bg-gray-900',
        textColor: 'text-gray-900',
        isImplemented: true,
    },
    {
        id: 'slack',
        name: 'Slack',
        description: 'Connect with your team workspace',
        icon: <MessageSquare className="w-6 h-6" />,
        color: 'bg-purple-600',
        textColor: 'text-purple-600',
        isImplemented: false,
    },
    {
        id: 'google_drive',
        name: 'Google Drive',
        description: 'Access and search your documents',
        icon: <Cloud className="w-6 h-6" />,
        color: 'bg-yellow-500',
        textColor: 'text-yellow-600',
        isImplemented: false,
    },
    {
        id: 'notion',
        name: 'Notion',
        description: 'Sync your pages and databases',
        icon: <FileText className="w-6 h-6" />,
        color: 'bg-gray-800',
        textColor: 'text-gray-800',
        isImplemented: false,
    },
];

const ConnectionModal: React.FC<ConnectionModalProps> = ({ isOpen, onClose, onConnect, loadingService }) => {
    const [searchTerm, setSearchTerm] = useState('');

    if (!isOpen) return null;

    const filteredServices = services.filter(s =>
        s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.description.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-gray-900/60 backdrop-blur-sm animate-in fade-in duration-300"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-300 border border-gray-100 flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="px-8 pt-8 pb-6 bg-gradient-to-b from-gray-50 to-white border-b border-gray-100 shrink-0">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-purple-100 rounded-2xl flex items-center justify-center">
                                <Plus className="w-6 h-6 text-purple-600" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-gray-900">Add Connection</h2>
                                <p className="text-sm text-gray-500">Connect your favorite tools to your AI agent</p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-400 hover:text-gray-600"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-purple-500 transition-colors" />
                        <input
                            type="text"
                            placeholder="Search for a service..."
                            className="w-full bg-white border border-gray-200 rounded-2xl py-3.5 pl-12 pr-4 text-sm outline-none focus:ring-4 focus:ring-purple-500/10 focus:border-purple-400 transition-all"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-8 space-y-8 min-h-0">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {filteredServices.map((service) => (
                            <button
                                key={service.id}
                                onClick={() => service.isImplemented && onConnect(service.id)}
                                disabled={!service.isImplemented || (loadingService != null)}
                                className={`flex items-start gap-4 p-5 rounded-2xl border transition-all text-left group overflow-hidden relative ${service.isImplemented
                                        ? 'bg-white border-gray-100 hover:border-purple-200 hover:shadow-lg hover:shadow-purple-500/5 cursor-pointer'
                                        : 'bg-gray-50/50 border-gray-100 opacity-70 cursor-not-allowed'
                                    }`}
                            >
                                {/* Active background glow */}
                                {service.isImplemented && (
                                    <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 via-purple-500/0 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                                )}

                                <div className={`w-12 h-12 ${service.color} rounded-xl flex items-center justify-center text-white shadow-lg shadow-${service.color.split('-')[1]}-500/20 group-hover:scale-110 transition-transform`}>
                                    {service.icon}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <h3 className="font-bold text-gray-900">{service.name}</h3>
                                        {service.isImplemented ? (
                                            <ArrowRight className="w-3 h-3 text-purple-400 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all font-bold" />
                                        ) : (
                                            <span className="text-[10px] font-bold text-gray-400 border border-gray-200 px-1.5 py-0.5 rounded uppercase">Soon</span>
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-500 leading-relaxed font-medium">
                                        {service.description}
                                    </p>
                                </div>

                                {loadingService === service.id && (
                                    <div className="absolute inset-0 bg-white/80 backdrop-blur-[1px] flex items-center justify-center animate-in fade-in">
                                        <Loader2 className="w-6 h-6 text-purple-600 animate-spin" />
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>

                    {filteredServices.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-12 text-center">
                            <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                                <Search className="w-8 h-8 text-gray-300" />
                            </div>
                            <h3 className="text-lg font-semibold text-gray-900">No services found</h3>
                            <p className="text-sm text-gray-500 max-w-xs mx-auto">
                                We couldn't find any services matching "{searchTerm}". Try a different search term.
                            </p>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-8 py-6 bg-gray-50 border-t border-gray-100 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-2 text-xs font-semibold text-gray-500">
                        <Shield className="w-4 h-4" />
                        Secure OAuth 2.0 Integration
                    </div>
                    <p className="text-[10px] text-gray-400 font-medium">
                        Request a service at <span className="text-purple-600">feedback@jadu.ai</span>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ConnectionModal;
