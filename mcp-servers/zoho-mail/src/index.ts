#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    Tool,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// Zoho Mail API base URL
const ZOHO_MAIL_API = 'https://mail.zoho.com/api';

// Get access token from environment
const getAccessToken = (): string => {
    const token = process.env.ZOHO_ACCESS_TOKEN;
    if (!token) {
        throw new Error('ZOHO_ACCESS_TOKEN environment variable is required');
    }
    return token;
};

// Helper to make Zoho API calls
async function zohoApiCall(endpoint: string, method: string = 'GET', data?: any) {
    const token = getAccessToken();

    try {
        const response = await axios({
            method,
            url: `${ZOHO_MAIL_API}${endpoint}`,
            headers: {
                'Authorization': `Zoho-oauthtoken ${token}`,
                'Content-Type': 'application/json',
            },
            data,
        });

        return response.data;
    } catch (error: any) {
        throw new Error(`Zoho API error: ${error.response?.data?.message || error.message}`);
    }
}

// Define tools
const tools: Tool[] = [
    {
        name: 'list_emails',
        description: 'List recent emails from Zoho Mail inbox',
        inputSchema: {
            type: 'object',
            properties: {
                accountId: {
                    type: 'string',
                    description: 'Zoho Mail account ID',
                },
                limit: {
                    type: 'number',
                    description: 'Number of emails to retrieve (default: 10)',
                    default: 10,
                },
                folderId: {
                    type: 'string',
                    description: 'Folder ID (default: inbox)',
                },
            },
            required: ['accountId'],
        },
    },
    {
        name: 'get_email',
        description: 'Get details of a specific email',
        inputSchema: {
            type: 'object',
            properties: {
                accountId: {
                    type: 'string',
                    description: 'Zoho Mail account ID',
                },
                messageId: {
                    type: 'string',
                    description: 'Email message ID',
                },
            },
            required: ['accountId', 'messageId'],
        },
    },
    {
        name: 'send_email',
        description: 'Send a new email via Zoho Mail',
        inputSchema: {
            type: 'object',
            properties: {
                accountId: {
                    type: 'string',
                    description: 'Zoho Mail account ID',
                },
                to: {
                    type: 'string',
                    description: 'Recipient email address',
                },
                subject: {
                    type: 'string',
                    description: 'Email subject',
                },
                body: {
                    type: 'string',
                    description: 'Email body content',
                },
            },
            required: ['accountId', 'to', 'subject', 'body'],
        },
    },
    {
        name: 'reply_to_email',
        description: 'Reply to an existing email',
        inputSchema: {
            type: 'object',
            properties: {
                accountId: {
                    type: 'string',
                    description: 'Zoho Mail account ID',
                },
                messageId: {
                    type: 'string',
                    description: 'Original message ID to reply to',
                },
                body: {
                    type: 'string',
                    description: 'Reply message body',
                },
            },
            required: ['accountId', 'messageId', 'body'],
        },
    },
    {
        name: 'search_emails',
        description: 'Search emails in Zoho Mail',
        inputSchema: {
            type: 'object',
            properties: {
                accountId: {
                    type: 'string',
                    description: 'Zoho Mail account ID',
                },
                query: {
                    type: 'string',
                    description: 'Search query',
                },
                limit: {
                    type: 'number',
                    description: 'Number of results (default: 10)',
                    default: 10,
                },
            },
            required: ['accountId', 'query'],
        },
    },
];

// Create server instance
const server = new Server(
    {
        name: 'zoho-mail-mcp',
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
            case 'list_emails': {
                const { accountId, limit = 10, folderId = 'inbox' } = args as any;
                const result = await zohoApiCall(
                    `/accounts/${accountId}/folders/${folderId}/messages?limit=${limit}`
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

            case 'get_email': {
                const { accountId, messageId } = args as any;
                const result = await zohoApiCall(
                    `/accounts/${accountId}/messages/${messageId}`
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

            case 'send_email': {
                const { accountId, to, subject, body } = args as any;
                const result = await zohoApiCall(
                    `/accounts/${accountId}/messages`,
                    'POST',
                    {
                        toAddress: to,
                        subject,
                        content: body,
                    }
                );

                return {
                    content: [
                        {
                            type: 'text',
                            text: `Email sent successfully! Message ID: ${result.data?.messageId || 'unknown'}`,
                        },
                    ],
                };
            }

            case 'reply_to_email': {
                const { accountId, messageId, body } = args as any;
                const result = await zohoApiCall(
                    `/accounts/${accountId}/messages/${messageId}/reply`,
                    'POST',
                    {
                        content: body,
                    }
                );

                return {
                    content: [
                        {
                            type: 'text',
                            text: `Reply sent successfully!`,
                        },
                    ],
                };
            }

            case 'search_emails': {
                const { accountId, query, limit = 10 } = args as any;
                const result = await zohoApiCall(
                    `/accounts/${accountId}/messages/search?searchKey=${encodeURIComponent(query)}&limit=${limit}`
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
    console.error('Zoho Mail MCP server running on stdio');
}

main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
});
