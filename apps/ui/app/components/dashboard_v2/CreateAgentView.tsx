import { FC, useState, useCallback, ReactNode } from "react";
import * as Icons from "lucide-react";
import {
    BookOpen,
    Plus,
    ArrowRight,
    ArrowLeft,
    Zap,
    Shield,
    Brain,
    Globe,
    Code,
    MessageSquare,
    Check,
    FileText,
    LayoutTemplate,
    Cpu,
    Database,
    Settings,
    Eye,
    Upload,
    Clock,
    Scissors,
    FileSearch,
    Lightbulb,
    Search,
    CheckCircle2,
    LayoutGrid,
    Boxes,
    Package,
    Scan,
    Wrench,
    ArrowUpRight,
    Loader2,
    Sparkles,
    PartyPopper,
    Rocket
} from "lucide-react";
import Stepper from "./Stepper";

interface CreateAgentViewProps {
    onBackToSources: () => void;
    onTabChange: (tab: 'sources' | 'create_agent') => void;
    activeTab: 'sources' | 'create_agent';
    onAgentInit: (agentData: any) => void;
}

const STEPS = [
    "Entry",
    "Details",
    "AI Config",
    "Instructions",
    "Knowledge",
    "Deep Agent",
    "Tools",
    "Review"
];

const PROVIDERS = [
    { id: 'openai', name: 'OpenAI', icon: '/icons/openai.svg', models: ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'] },
    { id: 'anthropic', name: 'Anthropic', icon: '/icons/anthropic.svg', models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'] },
    { id: 'azure', name: 'Azure OpenAI', icon: '/icons/azure.svg', models: ['gpt-4-32k', 'gpt-35-turbo-16k'] },
    { id: 'google', name: 'Google Gemini', icon: '/icons/google.svg', models: ['gemini-1.5-pro', 'gemini-1.5-flash'] },
];

const DEEP_AGENTS = [
    { id: 'researcher', name: 'Deep Researcher', icon: <Globe className="w-5 h-5" />, description: 'Exhaustive data gathering and analysis across multiple sources.' },
    { id: 'analyst', name: 'Data Analyst', icon: <Brain className="w-5 h-5" />, description: 'Specializes in numerical data, trends, and complex pattern recognition.' },
    { id: 'engineer', name: 'Systems Engineer', icon: <Code className="w-5 h-5" />, description: 'Expert in architecture, technical specs, and implementation planning.' },
];

interface ToolCapability {
    id: string;
    label: string;
    icon: ReactNode;
}

const TOOL_CAPABILITIES: ToolCapability[] = [
    { id: 'transcription', label: 'Transcription', icon: <Clock className="w-4 h-4" /> },
    { id: 'summarization', label: 'Summarization', icon: <Scissors className="w-4 h-4" /> },
    { id: 'extraction', label: 'Information Extraction', icon: <FileSearch className="w-4 h-4" /> },
    { id: 'analysis', label: 'Contextual Analysis', icon: <Lightbulb className="w-4 h-4" /> },
    { id: 'decision', label: 'Decision Support', icon: <Zap className="w-4 h-4" /> },
];

const TOOL_CATEGORIES = [
    { id: 'all', label: 'All', icon: <Icons.LayoutGrid size={18} />, description: 'All tools and providers' },
    { id: 'stackai', label: 'By StackAI', icon: <Icons.Boxes size={18} />, description: 'Native Stack AI tools and integrations', isVerified: true },
    { id: 'apps', label: 'Apps', icon: <Icons.Package size={18} />, description: 'Third-party applications and services' },
    { id: 'llm', label: 'LLM', icon: <Icons.Brain size={18} />, description: 'Large language models and AI services' },
    { id: 'databases', label: 'Databases', icon: <Icons.Database size={18} />, description: 'Database connections and data management' },
    { id: 'scrapers', label: 'Scrapers', icon: <Icons.Scan size={18} />, description: 'Web scraping and data extraction tools' },
    { id: 'custom', label: 'Custom Tools', icon: <Icons.Settings size={18} />, description: 'User-defined custom logic and APIs' },
];

const TOOLS = [
    // Databases
    { id: 'oracle', name: 'Oracle', category: 'databases', icon: <Icons.Database className="text-red-600" />, description: 'Query and insert data into an Oracle database' },
    { id: 'oracle_db', name: 'Oracle Database', category: 'databases', icon: <Icons.Database className="text-red-700" />, description: 'Connect to Oracle Database for enterprise data' },
    { id: 'postgres', name: 'PostgreSQL', category: 'databases', icon: <Icons.Database className="text-blue-600" />, description: 'Query a PostgreSQL database.' },
    { id: 'aws_rds', name: 'AWS RDS', category: 'databases', icon: <Icons.Database className="text-blue-500" />, description: 'Connect to AWS RDS managed relational data' },
    { id: 'aws_s3', name: 'AWS S3', category: 'databases', icon: <Icons.Database className="text-orange-500" />, description: 'Connect to AWS S3 for cloud storage and files' },
    { id: 'snowflake', name: 'Snowflake', category: 'databases', icon: <Icons.Database className="text-cyan-400" />, description: 'Query a Snowflake database.' },
    { id: 'aws_sqs', name: 'AWS SQS', category: 'databases', icon: <Icons.Database className="text-orange-600" />, description: 'Connect to AWS SQS to manage your queues' },
    { id: 'synapse', name: 'Synapse', category: 'databases', icon: <Icons.Database className="text-blue-400" />, description: 'Query a Synapse database.' },
    // LLM
    { id: 'openai_tool', name: 'OpenAI GPT', category: 'llm', icon: <Icons.Cpu className="text-emerald-500" />, description: 'Advanced reasoning and text generation.' },
    { id: 'anthropic_tool', name: 'Anthropic Claude', category: 'llm', icon: <Icons.Brain className="text-orange-500" />, description: 'Nuanced conversation and analysis.' },
    // Apps
    { id: 'slack', name: 'Slack', category: 'apps', icon: <Icons.MessageSquare className="text-purple-500" />, description: 'Send messages and interact with channels.' },
    { id: 'discord', name: 'Discord', category: 'apps', icon: <Icons.MessageSquare className="text-indigo-500" />, description: 'Connect your agent to Discord servers.' },
    { id: 'notion', name: 'Notion', category: 'apps', icon: <Icons.FileText className="text-gray-900" />, description: 'Sync notes and databases with Notion.' },
    // Scrapers
    { id: 'web_scraper', name: 'Web Scraper', category: 'scrapers', icon: <Icons.Globe className="text-blue-600" />, description: 'Extract clean data from any website.' },
];

const SUB_AGENTS = [
    { id: 'critic', name: 'The Critic', icon: <Shield className="w-4 h-4" />, description: 'Challenges assumptions and finds flaws.' },
    { id: 'synthesizer', name: 'Synthesizer', icon: <Zap className="w-4 h-4" />, description: 'Combines multiple viewpoints into one.' },
    { id: 'summarizer', name: 'Summarizer', icon: <FileText className="w-4 h-4" />, description: 'Distills complex info into brief bullet points.' },
    { id: 'translator', name: 'Translator', icon: <Globe className="w-4 h-4" />, description: 'Explains technical jargon in simple terms.' },
    { id: 'coder', name: 'Code Expert', icon: <Code className="w-4 h-4" />, description: 'Provides implementation details and snippets.' },
    { id: 'writer', name: 'Professional Writer', icon: <MessageSquare className="w-4 h-4" />, description: 'Polishes the final output for readability.' },
];

const CreateAgentView: FC<CreateAgentViewProps> = ({ onTabChange, activeTab, onAgentInit }) => {
    const [step, setStep] = useState(1);
    const [agentName, setAgentName] = useState("");
    const [agentDescription, setAgentDescription] = useState("");
    const [provider, setProvider] = useState("");
    const [model, setModel] = useState("");
    const [instructions, setInstructions] = useState("");
    const [selectedDeepAgents, setSelectedDeepAgents] = useState<string[]>([]);

    // Step 7: Tool Config State
    const [toolConfigs, setToolConfigs] = useState<Record<string, { enabled: boolean, capabilities: string[] }>>({});
    const [activeCategory, setActiveCategory] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');

    // Initialization States
    const [isInitializing, setIsInitializing] = useState(false);
    const [showSuccess, setShowSuccess] = useState(false);
    const [initStatus, setInitStatus] = useState("Initializing deployment...");
    const [initProgress, setInitProgress] = useState(0);

    const handleNext = () => setStep(prev => Math.min(prev + 1, 8));
    const handleBack = () => setStep(prev => Math.max(prev - 1, 1));

    const toggleDeepAgent = (id: string) => {
        setSelectedDeepAgents(prev =>
            prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
        );
    };

    const toggleTool = (toolId: string) => {
        setToolConfigs(prev => {
            const current = prev[toolId] || { enabled: false, capabilities: [] };
            return {
                ...prev,
                [toolId]: { ...current, enabled: !current.enabled }
            };
        });
    };

    const toggleCapability = (toolId: string, capId: string) => {
        setToolConfigs(prev => {
            const current = prev[toolId] || { enabled: true, capabilities: [] };
            const caps = current.capabilities.includes(capId)
                ? current.capabilities.filter(c => c !== capId)
                : [...current.capabilities, capId];
            return {
                ...prev,
                [toolId]: { ...current, capabilities: caps }
            };
        });
    };

    const toggleAllCapabilities = (toolId: string, enable: boolean) => {
        setToolConfigs(prev => ({
            ...prev,
            [toolId]: {
                ...(prev[toolId] || { enabled: true }),
                capabilities: enable ? TOOL_CAPABILITIES.map(c => c.id) : []
            }
        }));
    };

    const filteredTools = TOOLS.filter(tool => {
        const matchesCategory = activeCategory === 'all' || tool.category === activeCategory;
        const matchesSearch = tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            tool.description.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesCategory && matchesSearch;
    });

    const handleInitialize = async () => {
        setIsInitializing(true);
        setInitProgress(0);

        const statuses = [
            { msg: "Synthesizing agent identity...", p: 20 },
            { msg: "Calibrating neural instructions...", p: 45 },
            { msg: "Equipping requested tools...", p: 70 },
            { msg: "Finalizing neural bridge...", p: 90 },
            { msg: "Agent online.", p: 100 }
        ];

        for (const status of statuses) {
            setInitStatus(status.msg);
            setInitProgress(status.p);
            await new Promise(resolve => setTimeout(resolve, 800));
        }

        setShowSuccess(true);
        setIsInitializing(false);

        // Auto-redirect after delay
        setTimeout(() => {
            onAgentInit({
                name: agentName,
                provider: provider,
                model: model,
                instructions: instructions
            });
        }, 3000);
    };

    const isStepValid = () => {
        if (step === 2) return agentName.trim() !== "" && agentDescription.trim() !== "";
        if (step === 3) return provider !== "" && model !== "";
        if (step === 4) return instructions.trim() !== "";
        if (step === 6) return selectedDeepAgents.length > 0;
        return true;
    };

    return (
        <div className="flex-1 flex flex-col bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden animate-in fade-in slide-in-from-left-4 duration-300">
            {/* Header / Tab Switcher */}
            <div className="p-4 border-b border-gray-100 bg-gray-50/50 flex items-center justify-between">
                <div className="flex bg-gray-100 p-1 rounded-xl max-w-sm">
                    <button
                        onClick={() => onTabChange('sources')}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium transition-all ${activeTab === 'sources' ? "bg-white text-purple-600 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
                    >
                        <BookOpen size={16} />
                        Sources
                    </button>
                    <button
                        onClick={() => onTabChange('create_agent')}
                        className={`flex-1 flex items-center justify-center gap-2 py-2 px-4 rounded-lg text-sm font-medium transition-all ${activeTab === 'create_agent' ? "bg-white text-purple-600 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}
                    >
                        <Plus size={16} />
                        Create Agent
                    </button>
                </div>

                {step > 1 && (
                    <div className="flex items-center gap-4 text-xs font-semibold text-gray-400">
                        <span>STEP {step} OF 8</span>
                        <div className="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div className="h-full bg-purple-600 transition-all duration-500" style={{ width: `${(step / 8) * 100}%` }} />
                        </div>
                    </div>
                )}
            </div>

            {/* Stepper (Only visible after step 1) */}
            {step > 1 && (
                <div className="bg-white border-b border-gray-100">
                    <Stepper currentStep={step} totalSteps={8} steps={STEPS} />
                </div>
            )}

            <div className="flex-1 overflow-y-auto p-8">
                <div className="max-w-4xl mx-auto space-y-8">

                    {/* STEP 1: Entry Point */}
                    {step === 1 && (
                        <div className="space-y-12 py-12 text-center">
                            <div className="space-y-4">
                                <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">How would you like to start?</h1>
                                <p className="text-gray-500 text-xl max-w-xl mx-auto">Create a custom agent from scratch or start with a pre-built template.</p>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8">
                                <button
                                    onClick={handleNext}
                                    className="group relative flex flex-col items-center p-12 rounded-3xl border-2 border-gray-100 bg-gray-50 hover:border-purple-500 hover:bg-purple-50/30 transition-all duration-500 hover:scale-[1.02] active:scale-95 animate-in slide-in-from-bottom-8 duration-700"
                                >
                                    <div className="w-20 h-20 bg-purple-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-purple-500/20 group-hover:scale-110 transition-transform duration-300 mb-8">
                                        <Plus size={40} />
                                    </div>
                                    <h2 className="text-2xl font-bold text-gray-900 mb-3">Create Agent</h2>
                                    <p className="text-gray-500 text-center">Configure a new agent with complete control over behavior and tools.</p>
                                </button>
                                <button
                                    className="group relative flex flex-col items-center p-12 rounded-3xl border-2 border-gray-100 bg-gray-50 hover:border-purple-500 hover:bg-purple-50/30 transition-all duration-500 opacity-80 cursor-not-allowed animate-in slide-in-from-bottom-8 duration-700 delay-100"
                                >
                                    <div className="w-20 h-20 bg-blue-600 rounded-2xl flex items-center justify-center text-white shadow-xl shadow-blue-500/20 mb-8">
                                        <LayoutTemplate size={40} />
                                    </div>
                                    <h2 className="text-2xl font-bold text-gray-900 mb-3">Use Template</h2>
                                    <p className="text-gray-500 text-center">Start with a pre-configured setup optimized for specific use cases.</p>
                                    <span className="absolute top-4 right-4 bg-gray-200 text-gray-600 text-[10px] font-bold px-2 py-1 rounded-full">COMING SOON</span>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* STEP 2: Basic Details */}
                    {step === 2 && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div className="space-y-4">
                                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                                    <Icons.Edit3 className="text-purple-600" />
                                    Basic Details
                                </h2>
                                <p className="text-gray-500">Give your agent a name and description that helps identify its purpose.</p>
                            </div>
                            <div className="space-y-8">
                                <div className="space-y-3">
                                    <label className="text-sm font-semibold text-gray-700 uppercase tracking-widest">Agent Name</label>
                                    <input
                                        type="text"
                                        value={agentName}
                                        onChange={(e) => setAgentName(e.target.value)}
                                        placeholder="e.g. Legal Compliance Bot"
                                        className="w-full bg-gray-50 border border-gray-200 focus:border-purple-400 focus:ring-4 focus:ring-purple-500/5 rounded-2xl p-4 text-lg outline-none transition-all placeholder:text-gray-300"
                                    />
                                </div>
                                <div className="space-y-3">
                                    <label className="text-sm font-semibold text-gray-700 uppercase tracking-widest">Agent Description</label>
                                    <textarea
                                        rows={4}
                                        value={agentDescription}
                                        onChange={(e) => setAgentDescription(e.target.value)}
                                        placeholder="Briefly describe what this agent does and who it's for..."
                                        className="w-full bg-gray-50 border border-gray-200 focus:border-purple-400 focus:ring-4 focus:ring-purple-500/5 rounded-2xl p-4 text-lg outline-none transition-all resize-none placeholder:text-gray-300"
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* STEP 3: AI Configuration */}
                    {step === 3 && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div className="space-y-4">
                                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                                    <Cpu className="text-purple-600" />
                                    AI Configuration
                                </h2>
                                <p className="text-gray-500">Choose the AI provider and specific model that will power your agent.</p>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-3">
                                    <label className="text-sm font-semibold text-gray-700 uppercase tracking-widest">AI Provider</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        {PROVIDERS.map(p => (
                                            <button
                                                key={p.id}
                                                onClick={() => { setProvider(p.id); setModel(""); }}
                                                className={`flex items-center gap-3 p-4 rounded-2xl border-2 transition-all ${provider === p.id
                                                    ? "border-purple-500 bg-purple-50 text-purple-700 shadow-sm"
                                                    : "border-gray-100 bg-gray-50 hover:border-gray-200 text-gray-600"}`}
                                            >
                                                <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center shadow-sm">
                                                    {p.id === 'openai' && <Zap size={18} className="text-emerald-500" />}
                                                    {p.id === 'anthropic' && <Globe size={18} className="text-orange-500" />}
                                                    {p.id === 'azure' && <Cpu size={18} className="text-blue-500" />}
                                                    {p.id === 'google' && <Brain size={18} className="text-red-500" />}
                                                </div>
                                                <span className="font-bold text-sm">{p.name}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div className="space-y-3">
                                    <label className="text-sm font-semibold text-gray-700 uppercase tracking-widest">AI Model</label>
                                    <div className="grid grid-cols-1 gap-2">
                                        {provider ? (
                                            PROVIDERS.find(p => p.id === provider)?.models.map(m => (
                                                <button
                                                    key={m}
                                                    onClick={() => setModel(m)}
                                                    className={`w-full flex items-center justify-between p-4 rounded-2xl border-2 transition-all ${model === m
                                                        ? "border-purple-500 bg-white text-purple-700 shadow-sm"
                                                        : "border-gray-100 bg-gray-50 hover:border-gray-200 text-gray-600"}`}
                                                >
                                                    <span className="font-semibold">{m}</span>
                                                    {model === m && <Check size={16} className="text-purple-600" />}
                                                </button>
                                            ))
                                        ) : (
                                            <div className="h-full border-2 border-dashed border-gray-200 rounded-2xl flex items-center justify-center p-8 bg-gray-50">
                                                <p className="text-gray-400 text-sm text-center">Select a provider first to see available models</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* STEP 4: Instructions */}
                    {step === 4 && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-right-4 duration-500 text-gray-900 font-sans">
                            <div className="space-y-4">
                                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                                    <Settings className="text-purple-600" />
                                    Instructions
                                </h2>
                                <p className="text-gray-500">Define how your agent should behave, its goals, and any constraints it must follow.</p>
                            </div>
                            <div className="space-y-3">
                                <label className="text-sm font-semibold text-gray-700 uppercase tracking-widest">System Instructions</label>
                                <textarea
                                    rows={12}
                                    value={instructions}
                                    onChange={(e) => setInstructions(e.target.value)}
                                    placeholder="You are a helpful assistant specialized in... Your goals are to... Follow these constraints..."
                                    className="w-full bg-gray-50 border border-gray-200 focus:border-purple-400 focus:ring-4 focus:ring-purple-500/5 rounded-2xl p-6 text-lg outline-none transition-all resize-none font-mono text-sm leading-relaxed"
                                />
                            </div>
                        </div>
                    )}

                    {/* STEP 5: Knowledge Base Setup */}
                    {step === 5 && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div className="space-y-4">
                                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                                    <Database className="text-purple-600" />
                                    Knowledge Base Setup
                                </h2>
                                <p className="text-gray-500">Upload documents that your agent will use as its source of truth.</p>
                            </div>
                            <div className="border-4 border-dashed border-gray-100 rounded-3xl p-16 flex flex-col items-center justify-center text-center space-y-6 hover:border-purple-200 hover:bg-purple-50/10 transition-all group">
                                <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center text-gray-400 group-hover:bg-purple-600 group-hover:text-white transition-all shadow-sm">
                                    <Upload size={32} />
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-xl font-bold text-gray-900">Upload Files</h3>
                                    <p className="text-gray-500">Drag and drop your PDF, DOC, or TXT files here</p>
                                </div>
                                <button className="bg-white border-2 border-gray-200 rounded-xl py-3 px-8 font-bold text-gray-700 hover:border-purple-400 hover:text-purple-600 transition-all shadow-sm">
                                    Select Files
                                </button>
                                <p className="text-[10px] text-gray-400">Supported formats: PDF, DOCX, TXT, MD (Max 50MB per file)</p>
                            </div>
                        </div>
                    )}

                    {/* STEP 6: Deep Agent Selection */}
                    {step === 6 && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div className="space-y-4">
                                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                                    <Eye className="text-purple-600" />
                                    Deep Agent Selection
                                </h2>
                                <p className="text-gray-500">Select one or more Deep Agent specialized personas for higher-level reasoning.</p>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                {DEEP_AGENTS.map((agent, i) => (
                                    <button
                                        key={agent.id}
                                        onClick={() => toggleDeepAgent(agent.id)}
                                        className={`relative flex flex-col items-start p-6 rounded-2xl border-2 text-left transition-all duration-500 animate-in slide-in-from-bottom-4 fill-mode-forwards ${selectedDeepAgents.includes(agent.id)
                                            ? "border-purple-500 bg-purple-50/50 shadow-md scale-[1.02]"
                                            : "border-gray-100 bg-gray-50 hover:border-gray-200 hover:scale-[1.01]"
                                            }`}
                                        style={{ animationDelay: `${i * 100}ms` }}
                                    >
                                        <div className={`p-3 rounded-xl mb-4 ${selectedDeepAgents.includes(agent.id) ? "bg-purple-600 text-white" : "bg-white text-gray-600 shadow-sm"}`}>
                                            {agent.icon}
                                        </div>
                                        <h3 className="font-bold text-gray-900 mb-1">{agent.name}</h3>
                                        <p className="text-xs text-gray-500 leading-relaxed">{agent.description}</p>
                                        {selectedDeepAgents.includes(agent.id) && (
                                            <div className="absolute top-4 right-4 text-purple-600">
                                                <div className="bg-purple-600 rounded-full p-1">
                                                    <Check size={12} className="text-white" />
                                                </div>
                                            </div>
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* STEP 7: Tool Configuration */}
                    {step === 7 && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div className="space-y-2">
                                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                                    <Icons.Wrench className="text-purple-600" />
                                    Tool Configuration
                                </h2>
                                <p className="text-gray-500 text-sm">Enable supporting sub-agents and configure their specific analysis capabilities.</p>
                            </div>

                            <div className="flex gap-8 h-[500px] border border-gray-100 rounded-3xl overflow-hidden shadow-sm">
                                {/* Left Sidebar: Categories */}
                                <div className="w-64 bg-gray-50/50 border-r border-gray-100 p-4 space-y-1 overflow-y-auto">
                                    <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-3 mb-2 block">Tool Categories</label>
                                    {TOOL_CATEGORIES.map(cat => (
                                        <button
                                            key={cat.id}
                                            onClick={() => setActiveCategory(cat.id)}
                                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${activeCategory === cat.id
                                                ? "bg-white text-purple-600 shadow-sm border border-gray-100"
                                                : "text-gray-500 hover:bg-gray-100/50 hover:text-gray-700"}`}
                                        >
                                            <div className={`p-2 rounded-lg ${activeCategory === cat.id ? "bg-purple-100 text-purple-600" : "bg-gray-200/50 text-gray-400"}`}>
                                                {cat.icon}
                                            </div>
                                            <div className="text-left min-w-0">
                                                <div className="text-xs font-bold truncate flex items-center gap-1">
                                                    {cat.label}
                                                    {cat.isVerified && <Icons.CheckCircle2 size={10} className="text-yellow-500 fill-yellow-500/20" />}
                                                </div>
                                                <div className="text-[9px] text-gray-400 truncate leading-tight">{cat.description}</div>
                                            </div>
                                        </button>
                                    ))}
                                </div>

                                {/* Right Content: Search & Grid */}
                                <div className="flex-1 flex flex-col bg-white overflow-hidden">
                                    <div className="p-4 border-b border-gray-50">
                                        <div className="relative">
                                            <Icons.Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                placeholder={`Search for a tool in ${activeCategory === 'all' ? 'Tools' : TOOL_CATEGORIES.find(c => c.id === activeCategory)?.label}...`}
                                                className="w-full bg-gray-50 border border-gray-100 rounded-xl py-3 pl-12 pr-4 text-sm outline-none focus:ring-2 focus:ring-purple-500/10 placeholder:text-gray-400 transition-all font-medium"
                                            />
                                        </div>
                                    </div>

                                    <div className="flex-1 overflow-y-auto p-6">
                                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                                            {filteredTools.map((tool, i) => {
                                                const config = toolConfigs[tool.id] || { enabled: false, capabilities: [] };

                                                return (
                                                    <div
                                                        key={tool.id}
                                                        className={`p-4 rounded-2xl border-2 transition-all duration-500 group animate-in slide-in-from-right-4 fill-mode-forwards ${config.enabled
                                                            ? "border-purple-200 bg-purple-50/20 shadow-sm"
                                                            : "border-gray-50 bg-white hover:border-gray-200"}`}
                                                        style={{ animationDelay: `${i * 50}ms` }}
                                                    >
                                                        <div className="flex items-start gap-4 mb-4">
                                                            <div className={`p-3 rounded-xl transition-all ${config.enabled ? "bg-purple-600 text-white shadow-lg shadow-purple-200" : "bg-gray-100 text-gray-400"}`}>
                                                                {tool.icon}
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center justify-between mb-1">
                                                                    <h3 className="font-bold text-sm text-gray-900 truncate">{tool.name}</h3>
                                                                    <div
                                                                        onClick={() => toggleTool(tool.id)}
                                                                        className={`w-10 h-5 rounded-full relative cursor-pointer transition-all ${config.enabled ? "bg-purple-600" : "bg-gray-200"}`}
                                                                    >
                                                                        <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-all ${config.enabled ? "translate-x-5" : "translate-x-0"}`} />
                                                                    </div>
                                                                </div>
                                                                <p className="text-[10px] text-gray-500 leading-relaxed line-clamp-2">{tool.description}</p>
                                                            </div>
                                                        </div>

                                                        {config.enabled && (
                                                            <div className="space-y-3 pt-3 border-t border-purple-100 animate-in slide-in-from-top-2">
                                                                <div className="flex flex-wrap gap-1.5">
                                                                    {TOOL_CAPABILITIES.map((cap) => (
                                                                        <button
                                                                            key={cap.id}
                                                                            onClick={() => toggleCapability(tool.id, cap.id)}
                                                                            className={`px-2 py-1 rounded-md text-[9px] font-bold border transition-all ${config.capabilities.includes(cap.id)
                                                                                ? "bg-purple-600 border-purple-600 text-white shadow-sm"
                                                                                : "bg-white border-gray-200 text-gray-500 hover:border-gray-300"}`}
                                                                        >
                                                                            {cap.label}
                                                                        </button>
                                                                    ))}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                            {filteredTools.length === 0 && (
                                                <div className="col-span-full py-12 text-center space-y-3">
                                                    <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-300">
                                                        <Icons.Search size={32} />
                                                    </div>
                                                    <p className="text-gray-400 text-sm font-medium">No tools found matching your search</p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* STEP 8: Review & Finalize */}
                    {step === 8 && (
                        <div className="space-y-10 animate-in fade-in slide-in-from-right-4 duration-500">
                            <div className="space-y-4">
                                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                                    <Icons.CheckCircle2 className="text-purple-600" />
                                    Review & Finalize
                                </h2>
                                <p className="text-gray-500">Double-check your configuration before initializing your agent.</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
                                {/* Details Card */}
                                <div className="bg-gray-50 rounded-3xl p-6 border border-gray-100 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="font-bold text-gray-900 uppercase tracking-widest text-[10px]">Basic Details</h3>
                                        <button onClick={() => setStep(2)} className="text-purple-600 text-xs font-bold flex items-center gap-1 hover:underline">
                                            Edit <ArrowUpRight size={10} />
                                        </button>
                                    </div>
                                    <div className="space-y-2">
                                        <p className="font-bold text-lg text-gray-900">{agentName || "Untitled Agent"}</p>
                                        <p className="text-sm text-gray-500 line-clamp-2">{agentDescription || "No description provided."}</p>
                                    </div>
                                </div>

                                {/* AI Config Card */}
                                <div className="bg-gray-50 rounded-3xl p-6 border border-gray-100 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="font-bold text-gray-900 uppercase tracking-widest text-[10px]">AI Config</h3>
                                        <button onClick={() => setStep(3)} className="text-purple-600 text-xs font-bold flex items-center gap-1 hover:underline">
                                            Edit <ArrowUpRight size={10} />
                                        </button>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-sm">
                                            <Cpu size={24} className="text-purple-600" />
                                        </div>
                                        <div>
                                            <p className="font-bold text-gray-900 uppercase text-xs tracking-wider">{provider || "Not Selected"}</p>
                                            <p className="text-sm text-gray-500 font-mono">{model || "No Model"}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Deep Agents Card */}
                                <div className="bg-gray-50 rounded-3xl p-6 border border-gray-100 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="font-bold text-gray-900 uppercase tracking-widest text-[10px]">Deep Agents</h3>
                                        <button onClick={() => setStep(6)} className="text-purple-600 text-xs font-bold flex items-center gap-1 hover:underline">
                                            Edit <ArrowUpRight size={10} />
                                        </button>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {selectedDeepAgents.length > 0 ? (
                                            selectedDeepAgents.map(id => (
                                                <span key={id} className="bg-white border border-gray-200 px-3 py-1.5 rounded-xl text-xs font-bold text-gray-700 shadow-sm">
                                                    {DEEP_AGENTS.find(a => a.id === id)?.name}
                                                </span>
                                            ))
                                        ) : (
                                            <p className="text-xs text-red-500">Required: Select at least one</p>
                                        )}
                                    </div>
                                </div>

                                {/* Tools Card */}
                                <div className="bg-gray-50 rounded-3xl p-6 border border-gray-100 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="font-bold text-gray-900 uppercase tracking-widest text-[10px]">Enabled Tools</h3>
                                        <button onClick={() => setStep(7)} className="text-purple-600 text-xs font-bold flex items-center gap-1 hover:underline">
                                            Edit <ArrowUpRight size={10} />
                                        </button>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {Object.entries(toolConfigs).filter(([_, c]) => c.enabled).length > 0 ? (
                                            Object.entries(toolConfigs).filter(([_, c]) => c.enabled).map(([id, c]) => (
                                                <div key={id} className="bg-white border border-gray-200 p-2 rounded-xl flex items-center gap-2 shadow-sm">
                                                    <span className="text-xs font-bold text-gray-800">{TOOLS.find(a => a.id === id)?.name}</span>
                                                    <span className="text-[10px] bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded-md">{c.capabilities.length} Caps</span>
                                                </div>
                                            ))
                                        ) : (
                                            <p className="text-xs text-gray-400 italic">No tools enabled yet.</p>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Navigation Bar (Except Step 1) */}
                    {step > 1 && (
                        <div className="pt-10 flex items-center justify-between border-t border-gray-100 mt-12 mb-8">
                            <button
                                onClick={handleBack}
                                className="group flex items-center gap-3 text-gray-500 hover:text-purple-600 font-bold transition-all px-4 py-2"
                            >
                                <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
                                <span>Back</span>
                            </button>

                            <div className="flex gap-4">
                                {step < 8 ? (
                                    <button
                                        disabled={!isStepValid()}
                                        onClick={handleNext}
                                        className="group flex items-center gap-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-200 text-white rounded-full py-4 px-10 font-bold transition-all shadow-xl shadow-purple-500/20 active:scale-95"
                                    >
                                        <span>Continue</span>
                                        <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
                                    </button>
                                ) : (
                                    <button
                                        onClick={handleInitialize}
                                        className="group flex items-center gap-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:scale-105 text-white rounded-full py-5 px-12 font-extrabold transition-all shadow-xl shadow-purple-500/30 active:scale-95"
                                    >
                                        <Check size={24} />
                                        <span>Initialize Agent</span>
                                    </button>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
            {/* INITIALIZATION OVERLAY */}
            {isInitializing && (
                <div className="absolute inset-0 z-50 bg-white/90 backdrop-blur-sm flex flex-col items-center justify-center p-12 text-center animate-in fade-in duration-500">
                    <div className="relative mb-8">
                        <div className="w-32 h-32 rounded-full border-4 border-gray-100 flex items-center justify-center relative overflow-hidden">
                            <div
                                className="absolute bottom-0 left-0 right-0 bg-purple-600 transition-all duration-700 ease-out"
                                style={{ height: `${initProgress}%`, opacity: 0.15 }}
                            />
                            <div className="relative animate-bounce">
                                <Rocket className="text-purple-600" size={48} />
                            </div>
                        </div>
                        <div className="absolute -top-2 -right-2">
                            <Loader2 className="text-purple-600 animate-spin" size={24} />
                        </div>
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-2xl font-bold text-gray-900 tracking-tight">{initStatus}</h3>
                        <div className="w-64 h-2 bg-gray-100 rounded-full mx-auto overflow-hidden">
                            <div
                                className="h-full bg-purple-600 transition-all duration-500 ease-out"
                                style={{ width: `${initProgress}%` }}
                            />
                        </div>
                        <p className="text-gray-400 text-sm font-medium animate-pulse mt-4">This usually takes a few seconds...</p>
                    </div>
                </div>
            )}

            {/* SUCCESS STATE */}
            {showSuccess && (
                <div className="absolute inset-0 z-50 bg-white flex flex-col items-center justify-center p-12 text-center animate-in fade-in duration-700">
                    <div className="relative mb-8">
                        <div className="w-32 h-32 bg-green-500 rounded-full flex items-center justify-center shadow-2xl shadow-green-200 animate-in zoom-in duration-500 fill-mode-forwards">
                            <Check className="text-white" size={64} />
                        </div>
                        <div className="absolute -top-4 -left-4 animate-bounce delay-100">
                            <Sparkles className="text-yellow-400" size={32} />
                        </div>
                        <div className="absolute -bottom-4 -right-4 animate-bounce delay-300">
                            <Sparkles className="text-purple-400" size={24} />
                        </div>
                    </div>

                    <div className="space-y-6 max-w-sm">
                        <div className="space-y-2">
                            <h3 className="text-4xl font-black text-gray-900 tracking-tighter">SUCCESS!</h3>
                            <p className="text-gray-500 text-lg font-medium">Your agent <span className="text-purple-600 font-bold">{agentName}</span> is ready for deployment.</p>
                        </div>

                        <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100 animate-in slide-in-from-bottom-4 duration-1000 delay-500">
                            <div className="flex items-center gap-3 text-left">
                                <div className="w-10 h-10 bg-white border border-gray-100 rounded-xl flex items-center justify-center shadow-sm">
                                    <Cpu size={20} className="text-purple-600" />
                                </div>
                                <div>
                                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Bridging Complete</p>
                                    <p className="text-xs font-bold text-gray-700">Studio Panel updated successfully</p>
                                </div>
                            </div>
                        </div>

                        <div className="flex items-center justify-center gap-2 text-purple-600 font-bold text-sm">
                            <Loader2 className="animate-spin" size={16} />
                            <span>Redirecting to Chat...</span>
                        </div>
                    </div>

                    <div className="fixed inset-0 pointer-events-none">
                        {[...Array(6)].map((_, i) => (
                            <div
                                key={i}
                                className="absolute animate-in fade-out duration-[3000ms]"
                                style={{
                                    top: `${Math.random() * 100}%`,
                                    left: `${Math.random() * 100}%`,
                                    transform: `rotate(${Math.random() * 360}deg)`
                                }}
                            >
                                <PartyPopper className={`text-purple-400/${Math.random() * 0.5 + 0.2}`} size={24} />
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default CreateAgentView;
