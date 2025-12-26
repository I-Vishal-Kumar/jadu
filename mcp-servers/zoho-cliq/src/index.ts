#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    Tool,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// Zoho Cliq API base URL
const ZOHO_CLIQ_API = 'https://cliq.zoho.com/api/v2';

// Get access token from environment
const getAccessToken = (): string => {
    const token = process.env.ZOHO_ACCESS_TOKEN;
    if (!token) {
        throw new Error('ZOHO_ACCESS_TOKEN environment variable is required');
    }
    return token;
};

// Helper to make Zoho Cliq API calls
async function cliqApiCall(endpoint: string, method: string = 'GET', data?: any) {
    const token = getAccessToken();

    try {
        const response = await axios({
            method,
            url: `${ZOHO_CLIQ_API}${endpoint}`,
            headers: {
                'Authorization': `Zoho-oauthtoken ${token}`,
                'Content-Type': 'application/json',
            },
            data,
        });

        return response.data;
    } catch (error: any) {
        throw new Error(`Zoho Cliq API error: ${error.response?.data?.message || error.message}`);
    }
}

// Define tools
const tools: Tool[] = [
    {
        name: 'list_channels',
        description: 'List all Zoho Cliq channels the user has access to',
        inputSchema: {
            type: 'object',
            properties: {},
        },
    },
    {
        name: 'get_messages',
        description: 'Get recent messages from a Zoho Cliq channel',
        inputSchema: {
            type: 'object',
            properties: {
                channelId: {
                    type: 'string',
                    description: 'Channel ID',
                },
                limit: {
                    type: 'number',
                    description: 'Number of messages to retrieve (default: 10)',
                    default: 10,
                },
            },
            required: ['channelId'],
        },
    },
    {
        name: 'send_message',
        description: 'Send a message to a Zoho Cliq channel',
        inputSchema: {
            type: 'object',
            properties: {
                channelId: {
                    type: 'string',
                    description: 'Channel ID',
                },
                text: {
                    type: 'string',
                    description: 'Message text',
                },
            },
            required: ['channelId', 'text'],
        },
    },
    {
        name: 'get_channel_info',
        description: 'Get information about a specific Zoho Cliq channel',
        inputSchema: {
            type: 'object',
            properties: {
                channelId: {
                    type: 'string',
                    description: 'Channel ID',
                },
            },
            required: ['channelId'],
        },
    },
];

// Create server instance
const server = new Server(
    {
        name: 'zoho-cliq-mcp',
        version: '1.0.0',
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// Handle list tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        switch (name) {
            case 'list_channels': {
                const result = await cliqApiCall('/channels');

                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case 'get_messages': {
                const { channelId, limit = 10 } = args as any;
                const result = await cliqApiCall(
                    `/channels/${channelId}/messages?limit=${limit}`
                );

                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case 'send_message': {
                const { channelId, text } = args as any;
                const result = await cliqApiCall(
                    `/channels/${channelId}/message`,
                    'POST',
                    { text }
                );

                return {
                    content: [
                        {
                            type: 'text',
                            text: `Message sent successfully!`,
                        },
                    ],
                };
            }

            case 'get_channel_info': {
                const { channelId } = args as any;
                const result = await cliqApiCall(`/channels/${channelId}`);

                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    } catch (error: any) {
        return {
            content: [
                {
                    type: 'text',
                    text: `Error: ${error.message}`,
                },
            ],
            isError: true,
        };
    }
});

// Start server
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('Zoho Cliq MCP server running on stdio');
}

main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
});
