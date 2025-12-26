#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
    Tool,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';

// Zoom API base URL
const ZOOM_API = 'https://api.zoom.us/v2';

// Get access token from environment
const getAccessToken = (): string => {
    const token = process.env.ZOOM_ACCESS_TOKEN;
    if (!token) {
        throw new Error('ZOOM_ACCESS_TOKEN environment variable is required');
    }
    return token;
};

// Helper to make Zoom API calls
async function zoomApiCall(endpoint: string, method: string = 'GET', data?: any) {
    const token = getAccessToken();

    try {
        const response = await axios({
            method,
            url: `${ZOOM_API}${endpoint}`,
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            data,
        });

        return response.data;
    } catch (error: any) {
        throw new Error(`Zoom API error: ${error.response?.data?.message || error.message}`);
    }
}

// Define tools
const tools: Tool[] = [
    {
        name: 'create_meeting',
        description: 'Create a new Zoom meeting',
        inputSchema: {
            type: 'object',
            properties: {
                topic: {
                    type: 'string',
                    description: 'Meeting topic/title',
                },
                startTime: {
                    type: 'string',
                    description: 'Meeting start time in ISO 8601 format (e.g., 2024-12-26T14:00:00Z)',
                },
                duration: {
                    type: 'number',
                    description: 'Meeting duration in minutes (default: 60)',
                    default: 60,
                },
                agenda: {
                    type: 'string',
                    description: 'Meeting agenda/description',
                },
            },
            required: ['topic'],
        },
    },
    {
        name: 'list_meetings',
        description: 'List upcoming Zoom meetings',
        inputSchema: {
            type: 'object',
            properties: {
                type: {
                    type: 'string',
                    description: 'Meeting type: scheduled, live, or upcoming (default: upcoming)',
                    default: 'upcoming',
                },
            },
        },
    },
    {
        name: 'get_meeting',
        description: 'Get details of a specific Zoom meeting',
        inputSchema: {
            type: 'object',
            properties: {
                meetingId: {
                    type: 'string',
                    description: 'Meeting ID',
                },
            },
            required: ['meetingId'],
        },
    },
    {
        name: 'delete_meeting',
        description: 'Delete a Zoom meeting',
        inputSchema: {
            type: 'object',
            properties: {
                meetingId: {
                    type: 'string',
                    description: 'Meeting ID to delete',
                },
            },
            required: ['meetingId'],
        },
    },
];

// Create server instance
const server = new Server(
    {
        name: 'zoom-mcp',
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
            case 'create_meeting': {
                const { topic, startTime, duration = 60, agenda } = args as any;

                const meetingData: any = {
                    topic,
                    type: startTime ? 2 : 1, // 2 = scheduled, 1 = instant
                    duration,
                };

                if (startTime) {
                    meetingData.start_time = startTime;
                }

                if (agenda) {
                    meetingData.agenda = agenda;
                }

                const result = await zoomApiCall('/users/me/meetings', 'POST', meetingData);

                return {
                    content: [
                        {
                            type: 'text',
                            text: `Meeting created successfully!\n\nJoin URL: ${result.join_url}\nMeeting ID: ${result.id}\nPassword: ${result.password || 'N/A'}`,
                        },
                    ],
                };
            }

            case 'list_meetings': {
                const { type = 'upcoming' } = args as any;
                const result = await zoomApiCall(`/users/me/meetings?type=${type}`);

                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case 'get_meeting': {
                const { meetingId } = args as any;
                const result = await zoomApiCall(`/meetings/${meetingId}`);

                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify(result, null, 2),
                        },
                    ],
                };
            }

            case 'delete_meeting': {
                const { meetingId } = args as any;
                await zoomApiCall(`/meetings/${meetingId}`, 'DELETE');

                return {
                    content: [
                        {
                            type: 'text',
                            text: `Meeting ${meetingId} deleted successfully!`,
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
    console.error('Zoom MCP server running on stdio');
}

main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
});
